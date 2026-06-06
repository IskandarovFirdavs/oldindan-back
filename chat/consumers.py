"""
WebSocket consumer for real-time booking chat.

Connection URL: ws://host/ws/chat/<booking_id>/

Authentication: pass JWT token as query param:
  ws://host/ws/chat/42/?token=<access_token>

Or send it as the first message:
  {"type": "authenticate", "token": "..."}

On connect:
  - Validates JWT
  - Checks user has access to this booking (guest or branch partner)
  - Joins channel group "booking_chat_<booking_id>"

On receive {"type": "chat_message", "text": "..."}:
  - Saves Message to DB
  - Broadcasts to all group members

On disconnect:
  - Leaves group
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

logger = logging.getLogger(__name__)


class BookingChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.booking_id = self.scope["url_route"]["kwargs"]["booking_id"]
        self.group_name = f"booking_chat_{self.booking_id}"
        self.user       = None

        # Try to authenticate from query string
        query_string = self.scope.get("query_string", b"").decode()
        token        = None
        for part in query_string.split("&"):
            if part.startswith("token="):
                token = part[6:]
                break

        if token:
            self.user = await self._authenticate(token)

        if self.user:
            has_access = await self._check_access()
            if has_access:
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                await self.accept()
                await self.send(text_data=json.dumps({
                    "type":    "connected",
                    "message": f"Connected to booking #{self.booking_id} chat",
                }))
                return

        # Accept connection but mark as unauthenticated; wait for authenticate message
        await self.accept()
        await self.send(text_data=json.dumps({
            "type":    "auth_required",
            "message": "Send {\"type\": \"authenticate\", \"token\": \"<jwt>\"}",
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON.")
            return

        msg_type = data.get("type")

        # Handle late authentication
        if msg_type == "authenticate":
            token = data.get("token")
            if not token:
                await self._send_error("Token required.")
                return
            self.user = await self._authenticate(token)
            if not self.user:
                await self._send_error("Invalid or expired token.")
                return
            has_access = await self._check_access()
            if not has_access:
                await self._send_error("You do not have access to this booking.")
                return
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send(text_data=json.dumps({
                "type":    "authenticated",
                "message": "Authentication successful.",
            }))
            return

        # Handle chat message
        if msg_type == "chat_message":
            if not self.user:
                await self._send_error("Not authenticated.")
                return
            text = (data.get("text") or "").strip()
            if not text:
                await self._send_error("Message text is required.")
                return
            if len(text) > 2000:
                await self._send_error("Message too long (max 2000 characters).")
                return

            message = await self._save_message(text)
            if message is None:
                await self._send_error("Cannot send message for this booking.")
                return

            # Broadcast to all participants in this booking's chat group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type":    "chat_message",
                    "message": {
                        "id":          message["id"],
                        "booking":     int(self.booking_id),
                        "sender":      message["sender_id"],
                        "sender_name": message["sender_name"],
                        "sender_role": message["sender_role"],
                        "text":        message["text"],
                        "is_read":     False,
                        "created_at":  message["created_at"],
                    },
                },
            )
            return

        await self._send_error(f"Unknown message type: {msg_type}")

    # ── Channel layer handler (called when group_send fires) ──

    async def chat_message(self, event):
        """Relay a broadcast message to this WebSocket connection."""
        await self.send(text_data=json.dumps({
            "type":    "chat_message",
            "message": event["message"],
        }))

    # ── Helpers ───────────────────────────────────────────────

    async def _send_error(self, detail: str):
        await self.send(text_data=json.dumps({"type": "error", "detail": detail}))

    @database_sync_to_async
    def _authenticate(self, token: str):
        """Decode JWT and return the User, or None."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from accounts.models import User
            decoded = AccessToken(token)
            return User.objects.get(id=decoded["user_id"], is_active=True)
        except Exception:
            return None

    @database_sync_to_async
    def _check_access(self) -> bool:
        """Return True if self.user has access to self.booking_id's chat."""
        from bookings.models import Booking
        from bookings.permissions import can_manage_branch_bookings

        try:
            booking = (
                Booking.objects.select_related("branch__brand", "user")
                .get(id=self.booking_id)
            )
        except Booking.DoesNotExist:
            return False

        self._booking = booking

        is_guest   = booking.user_id == self.user.id
        is_partner = can_manage_branch_bookings(self.user, booking.branch)
        return is_guest or is_partner

    @database_sync_to_async
    def _save_message(self, text: str):
        """Save a Message to DB and return a dict of its data."""
        from bookings.models import Booking, Message

        try:
            booking = Booking.objects.select_related("branch__brand", "user").get(
                id=self.booking_id
            )
        except Booking.DoesNotExist:
            return None

        if booking.status in ["completed", "canceled", "no_show"]:
            return None

        message = Message.objects.create(
            booking=booking,
            sender=self.user,
            text=text,
        )

        u = self.user
        return {
            "id":          message.id,
            "sender_id":   u.id,
            "sender_name": f"{u.first_name} {u.last_name}".strip() or u.phone or "User",
            "sender_role": u.role,
            "text":        text,
            "created_at":  message.created_at.isoformat(),
        }