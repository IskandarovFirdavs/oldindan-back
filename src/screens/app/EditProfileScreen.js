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

const EditProfileScreen = ({ navigation }) => {
  const { user, updateUser } = useContext(AuthContext);
  const { colors } = useContext(ThemeContext);
  const { t } = useTranslation();

  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [loading, setLoading] = useState(false);

  const handleSaveProfile = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.updateProfile({
        first_name: firstName,
        last_name: lastName,
        email,
      });

      await updateUser(response.data);
      Alert.alert(t('common.success'), t('profile.save_profile'));
      navigation.goBack();
    } catch (error) {
      Alert.alert(t('errors.error'), error.message || t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const styles = createStyles(colors);

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>{t('profile.edit_profile')}</Text>
      </View>

      {/* Form */}
      <View style={styles.formContainer}>
        <Text style={[styles.label, { color: colors.text }]}>
          {t('profile.first_name')}
        </Text>
        <TextInput
          style={[styles.input, { borderColor: colors.border, color: colors.text }]}
          value={firstName}
          onChangeText={setFirstName}
          editable={!loading}
        />

        <Text style={[styles.label, { color: colors.text }, { marginTop: 16 }]}>
          {t('profile.last_name')}
        </Text>
        <TextInput
          style={[styles.input, { borderColor: colors.border, color: colors.text }]}
          value={lastName}
          onChangeText={setLastName}
          editable={!loading}
        />

        <Text style={[styles.label, { color: colors.text }, { marginTop: 16 }]}>
          {t('profile.email')}
        </Text>
        <TextInput
          style={[styles.input, { borderColor: colors.border, color: colors.text }]}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          editable={!loading}
        />

        <TouchableOpacity
          style={[styles.button, { backgroundColor: colors.primary }]}
          onPress={handleSaveProfile}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>{t('common.save')}</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const createStyles = (colors) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      backgroundColor: colors.surface,
    },
    backButton: {
      fontSize: 14,
      marginRight: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: 'bold',
    },
    formContainer: {
      padding: 16,
    },
    label: {
      fontSize: 14,
      fontWeight: '600',
      marginBottom: 8,
    },
    input: {
      borderWidth: 1,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 10,
      fontSize: 16,
    },
    button: {
      borderRadius: 8,
      paddingVertical: 12,
      alignItems: 'center',
      marginTop: 20,
    },
    buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
  });

export default EditProfileScreen;
