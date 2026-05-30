from django.utils import timezone

def is_branch_open(branch, check_time=None):
    """Branch ishlayaptimi tekshirish"""
    if check_time is None:
        check_time = timezone.now()
    
    weekday = check_time.strftime('%a').lower()
    working_hours = branch.working_hours or {}
    
    if weekday not in working_hours:
        return False
    
    open_time = working_hours[weekday][0]
    close_time = working_hours[weekday][1]
    
    current = check_time.strftime('%H:%M')
    
    return open_time <= current < close_time

def get_branch_open_time(branch, date):
    """Berilgan kundagi ochilish vaqtini qaytaradi"""
    weekday = date.strftime('%a').lower()
    working_hours = branch.working_hours or {}
    
    if weekday not in working_hours:
        return None
    
    return working_hours[weekday][0]

def get_branch_close_time(branch, date):
    """Berilgan kundagi yopilish vaqtini qaytaradi"""
    weekday = date.strftime('%a').lower()
    working_hours = branch.working_hours or {}
    
    if weekday not in working_hours:
        return None
    
    return working_hours[weekday][1]

def validate_booking_working_hours(branch, booking_start, booking_end):
    """Booking vaqtida branch ishlayotganligini tekshirish"""
    start_weekday = booking_start.strftime('%a').lower()
    working_hours = branch.working_hours or {}
    
    if start_weekday not in working_hours:
        raise ValueError(f"Branch {booking_start.strftime('%A')} kuni ishlamaydi")
    
    open_time = working_hours[start_weekday][0]
    close_time = working_hours[start_weekday][1]
    
    booking_time = booking_start.strftime('%H:%M')
    
    if booking_time < open_time:
        raise ValueError(f"Branch soat {open_time} da ochiladi")
    
    if booking_time >= close_time:
        raise ValueError(f"Branch soat {close_time} da yopiladi")
    
    # Booking_end ham ish vaqtida tugashini tekshirish
    end_time = booking_end.strftime('%H:%M')
    if end_time > close_time:
        raise ValueError(f"Booking soat {close_time} dan oldin tugashi kerak")