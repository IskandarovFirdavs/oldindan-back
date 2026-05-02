import React, { useState, useContext, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { initializeAPI } from '../../services/api';

const SettingsScreen = ({ navigation }) => {
  const { isDarkMode, toggleDarkMode, colors, language, changeLanguage, apiBaseUrl, updateApiUrl, languages } = useContext(ThemeContext);
  const { t, i18n } = useTranslation();
  const [newApiUrl, setNewApiUrl] = useState(apiBaseUrl);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setNewApiUrl(apiBaseUrl);
  }, [apiBaseUrl]);

  const handleSaveApiUrl = async () => {
    if (!newApiUrl.trim()) {
      Alert.alert(t('errors.error'), 'URL cannot be empty');
      return;
    }

    setSaving(true);
    try {
      // Initialize API with new URL
      initializeAPI(newApiUrl);
      await updateApiUrl(newApiUrl);
      Alert.alert(t('common.success'), 'API URL updated successfully');
    } catch (error) {
      Alert.alert(t('errors.error'), 'Failed to update API URL');
    } finally {
      setSaving(false);
    }
  };

  const handleLanguageChange = async (lang) => {
    await changeLanguage(lang);
    await i18n.changeLanguage(lang);
  };

  const styles = createStyles(colors);

  const SettingRow = ({ label, children }) => (
    <View style={[styles.settingRow, { borderBottomColor: colors.border }]}>
      <Text style={[styles.settingLabel, { color: colors.text }]}>{label}</Text>
      {children}
    </View>
  );

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>{t('settings.title')}</Text>
      </View>

      {/* Dark Mode */}
      <View style={[styles.section, { backgroundColor: colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          {t('settings.title')}
        </Text>

        <SettingRow label={t('settings.dark_mode')}>
          <Switch
            value={isDarkMode}
            onValueChange={toggleDarkMode}
            trackColor={{ false: '#ccc', true: colors.primary }}
            thumbColor={isDarkMode ? colors.primary : '#f4f3f4'}
          />
        </SettingRow>

        {/* Language Selection */}
        <View style={[styles.settingRow, { borderBottomColor: colors.border }]}>
          <Text style={[styles.settingLabel, { color: colors.text }]}>
            {t('settings.language')}
          </Text>
          <View style={styles.languageButtons}>
            {Object.entries(languages).map(([code, lang]) => (
              <TouchableOpacity
                key={code}
                style={[
                  styles.languageButton,
                  language === code && { backgroundColor: colors.primary },
                  language !== code && { borderColor: colors.border },
                ]}
                onPress={() => handleLanguageChange(code)}
              >
                <Text
                  style={[
                    styles.languageButtonText,
                    { color: language === code ? '#fff' : colors.text },
                  ]}
                >
                  {lang.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>

      {/* API Configuration */}
      <View style={[styles.section, { backgroundColor: colors.surface }, { marginTop: 12 }]}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          {t('settings.api_url')}
        </Text>

        <View style={styles.apiSection}>
          <Text style={[styles.apiDescription, { color: colors.textSecondary }]}>
            {t('settings.api_url_description')}
          </Text>

          <TextInput
            style={[styles.apiInput, { borderColor: colors.border, color: colors.text }]}
            placeholder={t('settings.api_url_placeholder')}
            placeholderTextColor={colors.textSecondary}
            value={newApiUrl}
            onChangeText={setNewApiUrl}
            editable={!saving}
          />

          <TouchableOpacity
            style={[styles.saveButton, { backgroundColor: colors.primary }]}
            onPress={handleSaveApiUrl}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>{t('common.save')}</Text>
            )}
          </TouchableOpacity>

          <Text style={[styles.apiHint, { color: colors.textSecondary }]}>
            Current: {apiBaseUrl}
          </Text>
        </View>
      </View>

      {/* Information */}
      <View style={[styles.section, { backgroundColor: colors.surface }, { marginTop: 12 }]}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          Information
        </Text>

        <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
          <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>
            App Version
          </Text>
          <Text style={[styles.infoValue, { color: colors.text }]}>1.0.0</Text>
        </View>

        <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
          <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>
            Built with React Native
          </Text>
        </View>
      </View>

      <View style={styles.spacer} />
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
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    backButton: {
      fontSize: 14,
      marginRight: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: 'bold',
    },
    section: {
      marginHorizontal: 12,
      marginTop: 12,
      borderRadius: 8,
      overflow: 'hidden',
    },
    sectionTitle: {
      fontSize: 14,
      fontWeight: 'bold',
      paddingHorizontal: 12,
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: 'rgba(0,0,0,0.1)',
    },
    settingRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 12,
      paddingVertical: 14,
      borderBottomWidth: 1,
    },
    settingLabel: {
      fontSize: 14,
      fontWeight: '500',
    },
    languageButtons: {
      flexDirection: 'row',
      gap: 8,
    },
    languageButton: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 6,
      borderWidth: 1,
    },
    languageButtonText: {
      fontSize: 12,
      fontWeight: '600',
    },
    apiSection: {
      paddingHorizontal: 12,
      paddingVertical: 14,
    },
    apiDescription: {
      fontSize: 12,
      marginBottom: 12,
    },
    apiInput: {
      borderWidth: 1,
      borderRadius: 6,
      paddingHorizontal: 12,
      paddingVertical: 10,
      marginBottom: 12,
      fontSize: 14,
    },
    saveButton: {
      borderRadius: 6,
      paddingVertical: 10,
      alignItems: 'center',
      marginBottom: 12,
    },
    saveButtonText: {
      color: '#fff',
      fontSize: 14,
      fontWeight: 'bold',
    },
    apiHint: {
      fontSize: 11,
      fontStyle: 'italic',
    },
    infoRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 14,
      borderBottomWidth: 1,
    },
    infoLabel: {
      fontSize: 14,
    },
    infoValue: {
      fontSize: 14,
      fontWeight: '600',
    },
    spacer: {
      height: 40,
    },
  });

export default SettingsScreen;
