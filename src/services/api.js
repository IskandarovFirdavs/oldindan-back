import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

let API_BASE_URL = 'http://localhost:8000';

// Initialize API client
export const initializeAPI = (baseUrl) => {
  API_BASE_URL = baseUrl;
};

export const getAPIBaseURL = () => API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('userToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const authAPI = {
  requestRegisterOTP: (phone) =>
    api.post('/api/users/register-otp/', { phone }),
  
  register: (data) =>
    api.post('/api/users/register/', data),
  
  login: (phone, code) =>
    api.post('/api/auth/login/', { phone, code }),
  
  requestForgotPassword: (phone) =>
    api.post('/api/users/forgot-password/', { phone }),
  
  confirmForgotPassword: (phone, code, password) =>
    api.post('/api/users/forgot-password-confirm/', { phone, code, password }),
  
  getMe: () =>
    api.get('/api/users/me/'),
  
  updateProfile: (data) =>
    api.patch('/api/users/me/', data),
};

// Restaurant endpoints
export const restaurantAPI = {
  getBranches: (params) =>
    api.get('/api/restaurants/branches/', { params }),
  
  getBranchDetail: (id) =>
    api.get(`/api/restaurants/branches/${id}/`),
  
  searchBranches: (query) =>
    api.get('/api/restaurants/branches/', { params: { search: query } }),
};

// Booking endpoints
export const bookingAPI = {
  getMyBookings: (params) =>
    api.get('/api/bookings/my/', { params }),
  
  getBookingDetail: (id) =>
    api.get(`/api/bookings/${id}/`),
  
  createBooking: (data) =>
    api.post('/api/bookings/', data),
  
  cancelBooking: (id, data) =>
    api.post(`/api/bookings/${id}/cancel/`, data),
};

// Notification endpoints
export const notificationAPI = {
  getNotifications: (params) =>
    api.get('/api/notifications/', { params }),
  
  markAsRead: (id) =>
    api.post(`/api/notifications/${id}/read/`),
};

// Favorites endpoints
export const favoriteAPI = {
  getFavorites: () =>
    api.get('/api/users/favorites/'),
  
  addFavorite: (branchId) =>
    api.post('/api/users/favorites/', { branch_id: branchId }),
  
  removeFavorite: (branchId) =>
    api.delete(`/api/users/favorites/${branchId}/`),
};

export default api;
