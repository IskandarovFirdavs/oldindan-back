# OLDINDAN Mobile App (React Native)

A full-featured React Native mobile application for the OLDINDAN restaurant booking platform, built with JavaScript (no TypeScript).

## Features

✅ **Authentication**
- Phone-based registration with OTP verification
- Phone-based login with OTP code
- Password reset functionality
- JWT token management with AsyncStorage

✅ **Restaurant Discovery**
- Interactive map showing available restaurants with coordinates
- Restaurant list with search functionality
- Restaurant detail pages with information
- Favorites/saved restaurants management

✅ **Booking System**
- Browse available restaurants on map
- Book tables with date/time selection
- Specify guest count and special requests
- View current and historical bookings
- Cancel bookings with notes
- Filter bookings by date and restaurant

✅ **User Management**
- User profile with avatar
- Edit profile information
- View and manage bookings
- Favorite restaurants
- Logout functionality

✅ **Notifications**
- Real-time notifications for booking updates
- Notification history
- Mark notifications as read
- Support for multiple notification types

✅ **Settings & Localization**
- 3 languages: Uzbek, Russian, English
- Dark/Light mode toggle
- Configurable API URL (for ngrok/backend connection)
- Persistent user preferences

✅ **Dark Mode**
- Full dark mode support
- Color scheme: Deep Red (#D7263D), Black, White
- Persistent theme preference

## Project Structure

```
oldindan-mobile/
├── src/
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── LoginScreen.js
│   │   │   ├── RegisterScreen.js
│   │   │   └── ForgotPasswordScreen.js
│   │   └── app/
│   │       ├── HomeScreen.js           (Map + Restaurants)
│   │       ├── SearchScreen.js
│   │       ├── RestaurantDetailScreen.js
│   │       ├── BookingFormScreen.js
│   │       ├── MyBookingsScreen.js
│   │       ├── ProfileScreen.js
│   │       ├── EditProfileScreen.js
│   │       ├── FavoritesScreen.js
│   │       ├── NotificationsScreen.js
│   │       └── SettingsScreen.js
│   ├── navigation/
│   │   └── RootNavigator.js            (All navigation stacks)
│   ├── context/
│   │   ├── AuthContext.js              (Auth state management)
│   │   └── ThemeContext.js             (Theme, language, settings)
│   ├── services/
│   │   └── api.js                      (API client with Axios)
│   ├── constants/
│   │   └── config.js                   (App constants & colors)
│   ├── locales/
│   │   ├── i18n.js                     (i18n setup)
│   │   ├── uz.json                     (Uzbek translations)
│   │   ├── ru.json                     (Russian translations)
│   │   └── en.json                     (English translations)
│   └── hooks/
│       └── (custom hooks as needed)
├── App.js                              (Main entry point)
├── app.json                            (Expo config)
└── package.json
```

## Installation & Setup

### Prerequisites

- Node.js 16+ and npm/yarn
- Expo CLI: `npm install -g expo-cli`
- Your Django backend running (with ngrok for mobile testing)

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Configure Backend URL

The app has a configurable API URL that defaults to `http://localhost:8000`. 

To change it:
1. Open the app
2. Go to **Profile** → **Settings**
3. Enter your backend URL (e.g., ngrok URL like `https://xxxx-xxxx-xxxx.ngrok.io`)
4. Tap **Save**

The URL is persisted in AsyncStorage, so it will be remembered across app sessions.

### 3. Run the App

```bash
# Start Expo development server
npm start

# Run on Android
npm run android

# Run on iOS (Mac only)
npm run ios

# Run on web
npm run web
```

## Backend Integration

The app expects your Django backend running with these endpoints:

### Authentication
- `POST /api/users/register-otp/` - Request OTP for registration
- `POST /api/users/register/` - Register new user with OTP
- `POST /api/auth/login/` - Login with phone & OTP code
- `POST /api/users/forgot-password/` - Request password reset OTP
- `POST /api/users/forgot-password-confirm/` - Reset password with OTP
- `GET /api/users/me/` - Get current user profile
- `PATCH /api/users/me/` - Update user profile

### Restaurants
- `GET /api/restaurants/branches/` - Get all active branches (with map coordinates)
- `GET /api/restaurants/branches/{id}/` - Get branch details

### Bookings
- `GET /api/bookings/my/` - Get user's bookings
- `POST /api/bookings/` - Create new booking
- `POST /api/bookings/{id}/cancel/` - Cancel booking

### Notifications
- `GET /api/notifications/` - Get all notifications
- `POST /api/notifications/{id}/read/` - Mark as read

### Favorites
- `GET /api/users/favorites/` - Get favorite branches
- `POST /api/users/favorites/` - Add to favorites
- `DELETE /api/users/favorites/{id}/` - Remove from favorites

## API Client Setup

The API client is configured in `src/services/api.js`:
- Uses Axios for HTTP requests
- Automatically adds JWT token from AsyncStorage to headers
- Base URL can be changed via Settings screen
- Supports error handling and request/response interceptors

## Using ngrok for Local Development

If running backend locally, use ngrok to expose it to mobile:

```bash
# Install ngrok
npm install -g ngrok

# Start ngrok tunnel (replace 8000 with your Django port)
ngrok http 8000

# Copy the HTTPS URL from ngrok output
# Example: https://1234-567-890.ngrok.io

# In app Settings, set API URL to: https://1234-567-890.ngrok.io
```

## Localization

The app supports 3 languages with full translation:
- **Uzbek (uz)** - Default
- **Russian (ru)**
- **English (en)**

To add/edit translations:
1. Edit the JSON files in `src/locales/`
2. Changes apply immediately with hot reload

## Dark Mode

Dark mode is fully supported with:
- `DARK_COLORS` theme in light theme
- `LIGHT_COLORS` for light mode
- Primary color: Deep Red (#D7263D)
- Toggle in Settings screen

## Color Scheme

- **Primary**: `#D7263D` (Deep Red)
- **Background**: `#FFFFFF` (light) / `#121212` (dark)
- **Surface**: `#F5F5F5` (light) / `#1E1E1E` (dark)
- **Text**: `#000000` (light) / `#FFFFFF` (dark)

## State Management

### AuthContext
- Manages user authentication state
- Token persistence with AsyncStorage
- Sign in/up/out functions
- User data management

### ThemeContext
- Dark/Light mode toggle
- Language switching
- API URL configuration
- Theme-specific colors

## Key Technologies

- **React Native** - Mobile framework
- **Expo** - Development platform
- **React Navigation** - Navigation (bottom tabs + stack)
- **Axios** - HTTP client
- **i18next** - Internationalization
- **React Native Maps** - Map display
- **AsyncStorage** - Data persistence
- **React Native Date Picker** - Date/time selection

## Notes

- The app uses JavaScript only (no TypeScript) as requested
- Phone numbers expected in format: numeric string (e.g., "998901234567")
- OTP codes are 6 digits
- All dates/times use ISO 8601 format
- JWT tokens stored securely in AsyncStorage
- Location permission requested on HomeScreen for map centering
- Notifications require permission grant

## License

All rights reserved - OLDINDAN 2024

## Support

For issues or questions:
1. Check the backend is running and accessible
2. Verify API URL in Settings
3. Check console logs: `npm start` shows errors
4. Ensure all permissions are granted in app settings

---

**Happy booking! 🎉**
