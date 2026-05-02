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

const RegisterScreen = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState('details'); // details | otp
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);
  const { signUp } = useContext(AuthContext);

  const handleSendOTP = async () => {
    if (!phone.trim() || !firstName.trim() || !lastName.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert(t('errors.error'), t('errors.passwords_not_match'));
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

  const handleRegister = async () => {
    if (!code.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.register({
        phone,
        first_name: firstName,
        last_name: lastName,
        password,
        code,
      });
      const result = await signUp({ phone, code }, () => Promise.resolve(response));
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
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.primary }]}>
          {t('auth.register_title')}
        </Text>
      </View>

      <View style={styles.formContainer}>
        {step === 'details' ? (
          <>
            <Text style={[styles.label, { color: colors.text }]}>
              {t('profile.first_name')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('profile.first_name')}
              placeholderTextColor={colors.textSecondary}
              value={firstName}
              onChangeText={setFirstName}
              editable={!loading}
            />

            <Text style={[styles.label, { color: colors.text }]}>
              {t('profile.last_name')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('profile.last_name')}
              placeholderTextColor={colors.textSecondary}
              value={lastName}
              onChangeText={setLastName}
              editable={!loading}
            />

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

            <Text style={[styles.label, { color: colors.text }]}>
              {t('common.password')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('common.password')}
              placeholderTextColor={colors.textSecondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              editable={!loading}
            />

            <Text style={[styles.label, { color: colors.text }]}>
              {t('common.confirm_password')}
            </Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text }]}
              placeholder={t('common.confirm_password')}
              placeholderTextColor={colors.textSecondary}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
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
              onPress={handleRegister}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>{t('common.register')}</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setStep('details')}>
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

export default RegisterScreen;
