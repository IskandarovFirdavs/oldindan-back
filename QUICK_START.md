# OLDINDAN Mobile App - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
npm install
```

### Step 2: Start Backend (if not already running)
```bash
cd ../v0-project  # Or wherever your Django backend is
python manage.py runserver
```

### Step 3: Setup ngrok (for mobile testing)
```bash
# In a new terminal
ngrok http 8000

# Copy the HTTPS URL shown (e.g., https://1234-xxxx.ngrok.io)
```

### Step 4: Run the App
```bash
npm start

# Choose:
# - Press 'a' for Android emulator
# - Press 'i' for iOS simulator (Mac only)
# - Press 'w' for web browser
# Or scan the QR code with Expo Go app on your phone
```

### Step 5: Configure API URL
1. Open the app
2. Tap **Profile** (bottom right)
3. Tap **Settings** (⚙️)
4. Paste your ngrok URL in "API URL"
5. Tap **Save**

## 📋 App Sections

### 🏠 **Home Tab**
- **Map View**: See all restaurants with coordinates
- **Your Location**: Tap menu to open/close
- **Recommended**: Swipe through nearby restaurants
- **Bell Icon**: View notifications (top right)

### 🔍 **Search Tab**
- Search for restaurants by name
- View results instantly
- Tap any restaurant for details

### 📅 **Bookings Tab**
- Current bookings (active tab)
- Booking history (History tab)
- Filter by date range and restaurant
- Cancel pending bookings

### 👤 **Profile Tab**
- View your profile
- Edit profile
- My Bookings
- Favorites
- Settings
- Logout

## 🔐 Authentication Flow

### 1️⃣ **Register**
- Enter phone: `998901234567` (Uzbekistan format)
- Receive OTP code
- Enter OTP (6 digits)
- Add name, email, password
- Confirm password
- Enter OTP again to verify

### 2️⃣ **Login**
- Enter phone number
- Receive OTP code
- Enter OTP code
- ✅ Logged in!

### 3️⃣ **Forgot Password**
- Enter phone number
- Receive OTP code
- Enter OTP code
- Set new password
- Confirm password
- ✅ Password reset!

## 🍽️ Booking Flow

1. **Find Restaurant**
   - Browse map on Home tab
   - Or search on Search tab
   - Or tap from Recommended list

2. **View Details**
   - See restaurant info, address, phone
   - Add to favorites (❤️)
   - Or proceed to book

3. **Book Table**
   - Tap "Book Table"
   - Select date & time
   - Enter number of guests
   - (Optional) Add children count
   - (Optional) Add special request
   - Tap "Confirm"
   - ✅ Booking created!

4. **Manage Booking**
   - View in **Bookings** tab
   - See booking status
   - Cancel if needed (pending bookings only)
   - View history

## ⚙️ Settings Options

### 🌙 **Dark Mode**
- Toggle dark/light mode
- Theme saves automatically

### 🌐 **Language**
- Choose: Uzbek, Russian, or English
- Instant language switch
- All content updates

### 🔗 **API URL**
- Change backend URL here
- For ngrok: paste HTTPS URL
- For local: `http://192.168.x.x:8000` (your IP)
- Must start with `http://` or `https://`

## 🎨 Color Scheme

The app uses a professional color scheme:
- **Primary Color**: Deep Red (`#D7263D`)
- **Light Mode**: White background with red accents
- **Dark Mode**: Dark gray background with red accents
- **Text**: High contrast for readability

## 📱 Using Expo Go for Testing

### Option 1: Scan QR Code
1. Install Expo Go app on your phone
2. Run: `npm start`
3. Scan the QR code displayed
4. App opens in Expo Go

### Option 2: Android Emulator
1. Install Android Studio
2. Start emulator: `npm run android`

### Option 3: iOS Simulator (Mac only)
1. Install Xcode
2. Start simulator: `npm run ios`

## 🐛 Troubleshooting

### "Cannot connect to backend"
- ✅ Check backend is running: `python manage.py runserver`
- ✅ Check API URL in Settings
- ✅ For ngrok, make sure to use HTTPS URL
- ✅ Check ngrok is still running

### "Phone number not valid"
- ✅ Use Uzbekistan format: `998901234567`
- ✅ Or format with +: `+998901234567`

### "OTP code not working"
- ✅ Check you entered correct 6-digit code
- ✅ Code expires after ~5 minutes
- ✅ Request new code if expired

### "Bookings not showing"
- ✅ Pull to refresh on Bookings tab
- ✅ Check you're logged in
- ✅ Check API connection

### "Map not showing"
- ✅ Grant location permission in app settings
- ✅ Ensure restaurants have latitude/longitude in database

## 📝 Code Structure

```
src/
├── screens/          ← All UI screens
├── navigation/       ← App navigation setup
├── context/          ← State management (Auth, Theme)
├── services/         ← API client
├── constants/        ← Colors, endpoints, configs
├── locales/          ← Translations (3 languages)
└── hooks/            ← Custom React hooks
```

## 🔄 State Management

- **AuthContext**: User login state, tokens
- **ThemeContext**: Dark mode, language, API URL
- **AsyncStorage**: Persistent data storage

## 🚨 Important Notes

- All times are in **ISO 8601 format** (e.g., `2024-05-15T14:30:00`)
- Phone numbers stored as **strings** (no country code needed)
- JWT tokens stored **securely in AsyncStorage**
- Booking duration: **1 hour by default** (adjustable in form)
- Max guests/children: **enter any number** (no validation limit)

## 📚 Languages Supported

- **Uzbek (O'zbek)** - Default
- **Russian (Русский)**
- **English**

All UI elements translated including:
- Buttons, labels, titles
- Error messages
- Notifications
- Status messages

## 🔔 Notifications

The app supports notifications for:
- Booking created
- Booking confirmed
- Booking canceled
- Booking reminders
- OTP codes

View all in **Notifications** screen (bell icon top right).

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Start your backend
3. ✅ Setup ngrok
4. ✅ Run the app
5. ✅ Configure API URL in Settings
6. ✅ Register & test booking flow

## 💡 Tips

- Use **ngrok** for testing from real phone
- Test **dark mode** in Settings
- Try all **3 languages** to see translations
- Test **notifications** after bookings
- Test **favorites** to save restaurants

---

**Ready to go? Run `npm start` now! 🚀**

For detailed documentation, see `MOBILE_APP_README.md`
