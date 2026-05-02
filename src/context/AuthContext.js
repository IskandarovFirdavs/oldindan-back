import React, { createContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = React.useReducer(
    (prevState, action) => {
      switch (action.type) {
        case 'RESTORE_TOKEN':
          return {
            ...prevState,
            userToken: action.token,
            isLoading: false,
            user: action.user,
          };
        case 'SIGN_IN':
          return {
            ...prevState,
            isSignout: false,
            userToken: action.token,
            user: action.user,
          };
        case 'SIGN_OUT':
          return {
            ...prevState,
            isSignout: true,
            userToken: null,
            user: null,
          };
        case 'SIGN_UP':
          return {
            ...prevState,
            isSignout: false,
            userToken: action.token,
            user: action.user,
          };
      }
    },
    {
      isLoading: true,
      isSignout: false,
      userToken: null,
      user: null,
    }
  );

  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const token = await AsyncStorage.getItem('userToken');
        const user = await AsyncStorage.getItem('userData');
        
        if (token) {
          dispatch({ type: 'RESTORE_TOKEN', token, user: user ? JSON.parse(user) : null });
        } else {
          dispatch({ type: 'RESTORE_TOKEN', token: null });
        }
      } catch (e) {
        dispatch({ type: 'RESTORE_TOKEN', token: null });
      }
    };

    bootstrapAsync();
  }, []);

  const authContext = {
    signIn: async (credentials, loginFn) => {
      try {
        const response = await loginFn(credentials);
        const { access, user } = response.data;
        
        await AsyncStorage.setItem('userToken', access);
        await AsyncStorage.setItem('userData', JSON.stringify(user));
        
        dispatch({ type: 'SIGN_IN', token: access, user });
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    signUp: async (data, registerFn) => {
      try {
        const response = await registerFn(data);
        const { access, user } = response.data;
        
        await AsyncStorage.setItem('userToken', access);
        await AsyncStorage.setItem('userData', JSON.stringify(user));
        
        dispatch({ type: 'SIGN_UP', token: access, user });
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    signOut: async () => {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userData');
      dispatch({ type: 'SIGN_OUT' });
    },
    signUp: async (userData, registerFn) => {
      try {
        const response = await registerFn(userData);
        const { access, user } = response.data;
        
        await AsyncStorage.setItem('userToken', access);
        await AsyncStorage.setItem('userData', JSON.stringify(user));
        
        dispatch({ type: 'SIGN_UP', token: access, user });
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    updateUser: async (user) => {
      await AsyncStorage.setItem('userData', JSON.stringify(user));
      dispatch({ type: 'SIGN_IN', token: state.userToken, user });
    },
  };

  return (
    <AuthContext.Provider value={{ ...state, ...authContext }}>
      {children}
    </AuthContext.Provider>
  );
};
