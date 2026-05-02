import React, { useState, useContext } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { AuthContext } from '../../context/AuthContext';
import { ThemeContext } from '../../context/ThemeContext';
import { authAPI } from '../../services/api';

const LoginScreen = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState('phone'); // phone | otp
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);
  const { signIn } = useContext(AuthContext);

  const handleSendOTP = async () => {
    if (!phone.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      await authAPI.requestRegisterOTP(phone);
      setStep('otp');
    } catch (error) {
      Alert.alert(t('errors.error'), error.message || t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!code.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.login(phone, code);
      const result = await signIn({ phone, code }, () => Promise.resolve(response));
      if (result.success) {
        navigation.reset({
          index: 0,
          routes: [{ name: 'Home' }],
        });
      }
    } catch (error) {
      Alert.alert(t('errors.error'), error.message || t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const styles = createStyles(colors);

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.primary }]}>
          {t('common.app_name')}
        </Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
          {step === 'phone' ? t('auth.login_title') : t('auth.otp_title')}
        </Text>
      </View>

      <View style={styles.formContainer}>
        {step === 'phone' ? (
          <>
            <Text style={[styles.label, { color: colors.text }]}>
              {t('auth.phone_label')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('auth.phone_label')}
              placeholderTextColor={colors.textSecondary}
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              editable={!loading}
            />
            <TouchableOpacity
              style={[styles.button, { backgroundColor: colors.primary }]}
              onPress={handleSendOTP}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>{t('common.next')}</Text>
              )}
            </TouchableOpacity>
          </>
        ) : (
          <>
            <Text style={[styles.label, { color: colors.text }]}>
              {t('auth.otp_description')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('auth.enter_otp')}
              placeholderTextColor={colors.textSecondary}
              value={code}
              onChangeText={setCode}
              keyboardType="numeric"
              maxLength={6}
              editable={!loading}
            />
            <TouchableOpacity
              style={[styles.button, { backgroundColor: colors.primary }]}
              onPress={handleLogin}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>{t('common.login')}</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setStep('phone')}>
              <Text style={[styles.link, { color: colors.primary }]}>
                {t('common.back')}
              </Text>
            </TouchableOpacity>
          </>
        )}

        <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}>
          <Text style={[styles.link, { color: colors.primary, marginTop: 20 }]}>
            {t('auth.forgot_password')}
          </Text>
        </TouchableOpacity>

        <View style={styles.registerContainer}>
          <Text style={[styles.registerText, { color: colors.textSecondary }]}>
            {t('common.register')}?{' '}
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={[styles.registerLink, { color: colors.primary }]}>
              {t('common.register')}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
};

const createStyles = (colors) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
      padding: 20,
    },
    header: {
      marginTop: 40,
      marginBottom: 40,
      alignItems: 'center',
    },
    title: {
      fontSize: 32,
      fontWeight: 'bold',
      marginBottom: 10,
    },
    subtitle: {
      fontSize: 16,
      marginBottom: 10,
    },
    formContainer: {
      marginBottom: 40,
    },
    label: {
      fontSize: 14,
      marginBottom: 8,
      fontWeight: '600',
    },
    input: {
      borderWidth: 1,
      borderColor: '#ddd',
      borderRadius: 8,
      paddingHorizontal: 16,
      paddingVertical: 12,
      marginBottom: 16,
      fontSize: 16,
    },
    button: {
      backgroundColor: colors.primary,
      borderRadius: 8,
      paddingVertical: 14,
      alignItems: 'center',
      marginBottom: 16,
    },
    buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
    link: {
      textAlign: 'center',
      fontSize: 14,
      marginBottom: 16,
    },
    registerContainer: {
      flexDirection: 'row',
      justifyContent: 'center',
      marginTop: 30,
    },
    registerText: {
      fontSize: 14,
    },
    registerLink: {
      fontSize: 14,
      fontWeight: 'bold',
    },
  });

export default LoginScreen;
