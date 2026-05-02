// API Configuration - Users can update from Settings
export const DEFAULT_API_BASE_URL = 'http://localhost:8000';

// Colors
export const COLORS = {
  primary: '#D7263D',
  black: '#000000',
  white: '#FFFFFF',
};

// Dark mode colors
export const DARK_COLORS = {
  primary: '#D7263D',
  background: '#121212',
  surface: '#1E1E1E',
  text: '#FFFFFF',
  textSecondary: '#BDBDBD',
  border: '#2C2C2C',
  success: '#4CAF50',
  error: '#F44336',
};

export const LIGHT_COLORS = {
  primary: '#D7263D',
  background: '#FFFFFF',
  surface: '#F5F5F5',
  text: '#000000',
  textSecondary: '#666666',
  border: '#E0E0E0',
  success: '#4CAF50',
  error: '#F44336',
};

// Languages
export const LANGUAGES = {
  uz: { label: 'O\'zbek', code: 'uz' },
  ru: { label: 'Русский', code: 'ru' },
  en: { label: 'English', code: 'en' },
};

export const DEFAULT_LANGUAGE = 'uz';

// API Endpoints
export const API_ENDPOINTS = {
  REGISTER_OTP: '/api/users/register-otp/',
  REGISTER: '/api/users/register/',
  LOGIN: '/api/auth/login/',
  FORGOT_PASSWORD: '/api/users/forgot-password/',
  FORGOT_PASSWORD_CONFIRM: '/api/users/forgot-password-confirm/',
  ME: '/api/users/me/',
  UPDATE_PROFILE: '/api/users/me/',
  BRANCHES: '/api/restaurants/branches/',
  BRANCH_DETAIL: '/api/restaurants/branches/{id}/',
  MY_BOOKINGS: '/api/bookings/my/',
  CREATE_BOOKING: '/api/bookings/',
  CANCEL_BOOKING: '/api/bookings/{id}/cancel/',
  NOTIFICATIONS: '/api/notifications/',
  MARK_NOTIFICATION_READ: '/api/notifications/{id}/read/',
  FAVORITES: '/api/users/favorites/',
};

export const BOOKING_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  CHECKED_IN: 'checked_in',
  COMPLETED: 'completed',
  CANCELED: 'canceled',
};
