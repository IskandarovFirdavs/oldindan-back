import React, { createContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DARK_COLORS, LIGHT_COLORS, DEFAULT_LANGUAGE, LANGUAGES } from '../constants/config';

export const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);
  const [apiBaseUrl, setApiBaseUrl] = useState('http://localhost:8000');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const darkMode = await AsyncStorage.getItem('isDarkMode');
      const lang = await AsyncStorage.getItem('language');
      const url = await AsyncStorage.getItem('apiBaseUrl');

      if (darkMode !== null) setIsDarkMode(JSON.parse(darkMode));
      if (lang !== null) setLanguage(lang);
      if (url !== null) setApiBaseUrl(url);
    } catch (error) {
      console.log('Error loading settings:', error);
    }
  };

  const toggleDarkMode = async () => {
    try {
      const newValue = !isDarkMode;
      setIsDarkMode(newValue);
      await AsyncStorage.setItem('isDarkMode', JSON.stringify(newValue));
    } catch (error) {
      console.log('Error saving dark mode:', error);
    }
  };

  const changeLanguage = async (lang) => {
    try {
      setLanguage(lang);
      await AsyncStorage.setItem('language', lang);
    } catch (error) {
      console.log('Error saving language:', error);
    }
  };

  const updateApiUrl = async (url) => {
    try {
      setApiBaseUrl(url);
      await AsyncStorage.setItem('apiBaseUrl', url);
    } catch (error) {
      console.log('Error saving API URL:', error);
    }
  };

  const colors = isDarkMode ? DARK_COLORS : LIGHT_COLORS;

  const value = {
    isDarkMode,
    toggleDarkMode,
    colors,
    language,
    changeLanguage,
    apiBaseUrl,
    updateApiUrl,
    languages: LANGUAGES,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};
