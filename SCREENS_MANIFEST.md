# OLDINDAN Mobile App - Complete Screens Manifest

## Overview
This document lists all 14 screens in the app with their features and navigation paths.

---

## Authentication Screens (Shown Before Login)

### 1. LoginScreen
**File**: `src/screens/auth/LoginScreen.js`

**Purpose**: Authenticate user with phone and OTP code

**Features**:
- Phone number input
- OTP code input (6 digits)
- 2-step authentication flow
- Navigation to Register
- Navigation to Forgot Password
- Loading states

**Props**: `{ navigation }`

**State**:
- `phone` - Phone number
- `code` - OTP code
- `step` - Current step (phone | otp)
- `loading` - Loading state

**API Calls**:
- `authAPI.requestRegisterOTP(phone)` - Request OTP
- `authAPI.login(phone, code)` - Login

**Navigation**:
- → Register (new user)
- → ForgotPassword
- → Home (success)

**Dark Mode**: ✅ Full support

---

### 2. RegisterScreen
**File**: `src/screens/auth/RegisterScreen.js`

**Purpose**: Create new user account with OTP verification

**Features**:
- First name input
- Last name input
- Phone number input
- Password input
- Password confirmation
- OTP verification
- 2-step registration flow

**Props**: `{ navigation }`

**State**:
- `phone`, `firstName`, `lastName`, `password`, `confirmPassword`, `code`
- `step` - Form step (details | otp)
- `loading`

**API Calls**:
- `authAPI.requestRegisterOTP(phone)` - Request OTP
- `authAPI.register({phone, first_name, last_name, password, code})` - Register

**Validation**:
- Required fields
- Password confirmation match
- Phone format

**Dark Mode**: ✅ Full support

---

### 3. ForgotPasswordScreen
**File**: `src/screens/auth/ForgotPasswordScreen.js`

**Purpose**: Reset forgotten password using OTP

**Features**:
- Phone number input
- OTP code input
- New password input
- Password confirmation
- 2-step password reset flow

**Props**: `{ navigation }`

**State**:
- `phone`, `code`, `password`, `confirmPassword`
- `step` - Form step (phone | otp)
- `loading`

**API Calls**:
- `authAPI.requestForgotPassword(phone)` - Request OTP
- `authAPI.confirmForgotPassword(phone, code, password)` - Reset password

**Dark Mode**: ✅ Full support

---

## Main App Screens (Shown After Login)

### 4. HomeScreen
**File**: `src/screens/app/HomeScreen.js`

**Purpose**: Show map with restaurants and recommended list

**Features**:
- Interactive map with all restaurants
- User's current location marker
- Restaurant markers (tappable)
- Recommended restaurants list
- Pull-to-refresh
- Menu button (open/close drawer)
- Notifications bell icon

**Props**: `{ navigation }`

**State**:
- `branches` - List of restaurants
- `location` - User's location
- `region` - Map region/zoom
- `loading`, `refreshing`

**API Calls**:
- `restaurantAPI.getBranches()` - Get all branches
- `Location.getCurrentPositionAsync()` - Get user location

**Map Features**:
- Centered on user location
- Markers for restaurants
- Tap marker → RestaurantDetail
- Distance calculation

**Dark Mode**: ✅ Full support

**Tab**: Home (default active)

---

### 5. SearchScreen
**File**: `src/screens/app/SearchScreen.js`

**Purpose**: Search for restaurants by name

**Features**:
- Search bar with keyboard
- Real-time search results
- Result list
- Auto-focus on search input
- Back button to close
- Loading state
- No results message

**Props**: `{ navigation }`

**State**:
- `searchText` - Search input
- `results` - Search results
- `loading`

**API Calls**:
- `restaurantAPI.searchBranches(query)` - Search branches

**Dark Mode**: ✅ Full support

**Tab**: Search

---

### 6. RestaurantDetailScreen
**File**: `src/screens/app/RestaurantDetailScreen.js`

**Purpose**: Show detailed information about a restaurant

**Features**:
- Restaurant name and brand
- Full address
- Phone number with call button
- Working hours
- Service fee
- Deposit information
- Favorite button (heart icon)
- Book table button
- Back navigation

**Props**: `{ route, navigation }`
- `route.params.branchId` - Branch ID

**State**:
- `branch` - Branch details
- `isFavorite` - Is favorited
- `loading`

**API Calls**:
- `restaurantAPI.getBranchDetail(branchId)` - Get details
- `favoriteAPI.addFavorite(branchId)` - Add favorite
- `favoriteAPI.removeFavorite(branchId)` - Remove favorite
- `Linking.openURL('tel:...')` - Call phone

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back
- → BookingForm (Book Table button)

---

### 7. BookingFormScreen
**File**: `src/screens/app/BookingFormScreen.js`

**Purpose**: Create new restaurant booking

**Features**:
- Date & time picker
- Number of guests input
- Number of children input
- Special request textarea
- Confirm button
- Loading state
- Error handling

**Props**: `{ route, navigation }`
- `route.params.branchId` - Which restaurant to book

**State**:
- `date` - Selected booking date
- `showDatePicker` - Date picker modal
- `guests` - Guest count
- `children` - Children count
- `specialRequest` - Special request text
- `loading`

**API Calls**:
- `bookingAPI.createBooking({...})` - Create booking

**Validations**:
- Minimum 1 guest
- Date cannot be in past
- End time = start time + 1 hour (default)

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back
- → MyBookings (success)

---

### 8. BookingDetailScreen
**File**: `src/screens/app/BookingDetailScreen.js`

**Purpose**: View booking details and manage it

**Features**:
- Booking status display
- Restaurant name and address
- Booking date & time
- Guest count
- Children count
- Special request
- Cancel button (if pending)
- Status color coding

**Props**: `{ route, navigation }`
- `route.params.bookingId` - Booking ID

**State**:
- `booking` - Booking details
- `loading`

**API Calls**:
- `bookingAPI.getBookingDetail(bookingId)` - Get details
- `bookingAPI.cancelBooking(bookingId, data)` - Cancel (if pending)

**Status Colors**:
- pending → warning
- confirmed → success
- completed → primary
- canceled → error

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back

---

### 9. MyBookingsScreen
**File**: `src/screens/app/MyBookingsScreen.js`

**Purpose**: View current and past bookings

**Features**:
- 2 tabs: Current & History
- Booking list cards
- Booking status display
- Restaurant name
- Date & time
- Guest count
- Edit button (→ BookingDetail)
- Cancel button (if pending)
- Pull-to-refresh
- Filter capabilities

**Props**: `{ navigation }`

**State**:
- `bookings` - List of bookings
- `activeTab` - Current tab (current | history)
- `loading`, `refreshing`

**API Calls**:
- `bookingAPI.getMyBookings({})` - Get bookings
- `bookingAPI.cancelBooking(id, data)` - Cancel booking

**Tab Filtering**:
- **Current**: Future bookings, not canceled
- **History**: Past bookings or canceled

**Dark Mode**: ✅ Full support

**Tab**: Bookings

---

### 10. ProfileScreen
**File**: `src/screens/app/ProfileScreen.js`

**Purpose**: User profile and main menu

**Features**:
- User avatar (initial)
- User name
- User phone
- Edit profile button (pencil icon)
- Menu buttons:
  - My Bookings
  - Favorites
  - Settings
  - Help & Support
  - About App
- Logout button
- Logout confirmation dialog

**Props**: `{ navigation }`

**State**: Uses AuthContext & ThemeContext

**Menu Navigation**:
- Edit Profile → EditProfileScreen
- My Bookings → MyBookingsScreen
- Favorites → FavoritesScreen
- Settings → SettingsScreen
- Help → Alert dialog
- About → Alert dialog
- Logout → SignOut + Login screen

**Dark Mode**: ✅ Full support

**Tab**: Profile

---

### 11. EditProfileScreen
**File**: `src/screens/app/EditProfileScreen.js`

**Purpose**: Update user profile information

**Features**:
- First name input (pre-filled)
- Last name input (pre-filled)
- Email input (pre-filled)
- Save button
- Back button
- Loading state
- Success confirmation

**Props**: `{ navigation }`

**State**:
- `firstName`, `lastName`, `email` - Form inputs
- `loading`

**API Calls**:
- `authAPI.updateProfile({first_name, last_name, email})` - Update

**Validation**:
- First name required
- Last name required

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back
- (auto-back on success)

---

### 12. FavoritesScreen
**File**: `src/screens/app/FavoritesScreen.js`

**Purpose**: View saved/favorite restaurants

**Features**:
- List of favorite restaurants
- Restaurant name
- Address
- Tap to view details
- Pull-to-refresh
- Empty state message
- Loading state

**Props**: `{ navigation }`

**State**:
- `favorites` - Favorite branches
- `loading`, `refreshing`

**API Calls**:
- `favoriteAPI.getFavorites()` - Get favorites

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back
- → RestaurantDetail (tap card)

---

### 13. NotificationsScreen
**File**: `src/screens/app/NotificationsScreen.js`

**Purpose**: View all notifications

**Features**:
- Notification list
- Notification title
- Notification body
- Timestamp
- Unread indicator (blue dot)
- Mark as read on tap
- Pull-to-refresh
- Empty state message
- Loading state

**Props**: `{ navigation }`

**State**:
- `notifications` - List of notifications
- `loading`, `refreshing`

**API Calls**:
- `notificationAPI.getNotifications({})` - Get notifications
- `notificationAPI.markAsRead(id)` - Mark as read

**Unread Indicator**: Left border + blue dot

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back

---

### 14. SettingsScreen
**File**: `src/screens/app/SettingsScreen.js`

**Purpose**: App settings and configuration

**Features**:
- Dark mode toggle switch
- Language selection (3 buttons)
- API URL configuration
  - Text input for URL
  - Save button
  - Current URL display
  - Help text
- App version display
- Pull-to-refresh
- Back button
- Persistent settings

**Props**: `{ navigation }`

**State**:
- `newApiUrl` - Edited API URL
- `saving` - Save loading state
- Uses ThemeContext for dark mode & language

**API Calls**:
- `updateApiUrl(url)` - Save API URL
- `toggleDarkMode()` - Toggle dark mode
- `changeLanguage(lang)` - Change language

**Language Options**:
- O'zbek (Uzbek)
- Русский (Russian)
- English

**Settings Persistence**:
- Dark mode → AsyncStorage
- Language → AsyncStorage
- API URL → AsyncStorage

**Dark Mode**: ✅ Full support

**Navigation**:
- ← Back

---

## Navigation Structure

### Stack 1: Auth (Before Login)
```
LoginScreen
  ├→ RegisterScreen
  └→ ForgotPasswordScreen
```

### Stack 2: Home Tab
```
HomeScreen
├→ RestaurantDetailScreen
├→ BookingFormScreen
└→ NotificationsScreen
```

### Stack 3: Search Tab
```
SearchScreen
├→ RestaurantDetailScreen
└→ BookingFormScreen
```

### Stack 4: Bookings Tab
```
MyBookingsScreen
├→ BookingDetailScreen
└→ RestaurantDetailScreen
```

### Stack 5: Profile Tab
```
ProfileScreen
├→ MyBookingsScreen
├→ EditProfileScreen
├→ FavoritesScreen
└→ SettingsScreen
```

### Tab Bar (4 tabs)
```
├ Home 🏠
├ Search 🔍
├ Bookings 📅
└ Profile 👤
```

---

## Screen Count Summary

| Category | Count |
|----------|-------|
| Auth Screens | 3 |
| Home Tab | 4 nested |
| Search Tab | 2 nested |
| Bookings Tab | 2 nested |
| Profile Tab | 5 nested |
| **Total Screens** | **14** |

---

## Shared Features

### All Screens Have:
- ✅ Dark mode support
- ✅ i18n (3 languages)
- ✅ Responsive layout
- ✅ Error handling
- ✅ Loading states
- ✅ Theme-based colors

### Most Screens Have:
- ✅ Pull-to-refresh
- ✅ Back button
- ✅ Error alerts
- ✅ Loading indicators

---

## Developer Notes

### Adding New Screens
1. Create file in `src/screens/app/NewScreen.js`
2. Use existing screens as templates
3. Add to RootNavigator.js
4. Update navigation as needed

### Styling Pattern
```javascript
const styles = createStyles(colors);
// Then:
style={[styles.container, { backgroundColor: colors.background }]}
```

### State Pattern
```javascript
const { colors } = useContext(ThemeContext);
const { t } = useTranslation();
```

### API Call Pattern
```javascript
try {
  const response = await apiCall(params);
  // Handle success
} catch (error) {
  Alert.alert(t('errors.error'), error.message);
}
```

---

## Performance Notes

- HomeScreen: FlatList for restaurants
- MyBookingsScreen: FlatList for bookings
- NotificationsScreen: FlatList for notifications
- SearchScreen: FlatList for results

All using `keyExtractor` and `scrollEnabled={false}` in nested lists.

---

**Total Estimated Lines of Code**: ~3,000+ lines
**Languages Supported**: 3 (Uzbek, Russian, English)
**API Endpoints Connected**: 20+
**Components/Screens**: 14
**Navigation Stacks**: 5 + Tab Navigation

All screens fully functional and production-ready! ✅
