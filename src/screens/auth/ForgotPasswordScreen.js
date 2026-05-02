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
import { ThemeContext } from '../../context/ThemeContext';
import { authAPI } from '../../services/api';

const ForgotPasswordScreen = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [step, setStep] = useState('phone'); // phone | otp
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  const handleSendOTP = async () => {
    if (!phone.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      await authAPI.requestForgotPassword(phone);
      setStep('otp');
    } catch (error) {
      Alert.alert(t('errors.error'), error.message || t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!code.trim() || !password.trim() || !confirmPassword.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert(t('errors.error'), t('errors.passwords_not_match'));
      return;
    }

    setLoading(true);
    try {
      await authAPI.confirmForgotPassword(phone, code, password);
      Alert.alert(t('common.success'), 'Password reset successfully');
      navigation.navigate('Login');
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
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.primary }]}>
          {t('auth.reset_password')}
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

            <Text style={[styles.label, { color: colors.text }]}>
              {t('auth.new_password')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('auth.new_password')}
              placeholderTextColor={colors.textSecondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              editable={!loading}
            />

            <Text style={[styles.label, { color: colors.text }]}>
              {t('auth.confirm_new_password')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('auth.confirm_new_password')}
              placeholderTextColor={colors.textSecondary}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
              editable={!loading}
            />

            <TouchableOpacity
              style={[styles.button, { backgroundColor: colors.primary }]}
              onPress={handleResetPassword}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>{t('auth.reset_password')}</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => { setStep('phone'); setCode(''); setPassword(''); setConfirmPassword(''); }}>
              <Text style={[styles.link, { color: colors.primary }]}>
                {t('common.back')}
              </Text>
            </TouchableOpacity>
          </>
        )}
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
      marginTop: 20,
      marginBottom: 30,
    },
    backButton: {
      fontSize: 14,
      marginBottom: 10,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
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
      borderRadius: 8,
      paddingVertical: 14,
      alignItems: 'center',
      marginBottom: 16,
      marginTop: 20,
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
  });

export default ForgotPasswordScreen;
