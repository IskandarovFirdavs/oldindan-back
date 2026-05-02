import React, { useState, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { AuthContext } from '../../context/AuthContext';
import { ThemeContext } from '../../context/ThemeContext';

const ProfileScreen = ({ navigation }) => {
  const { user, signOut } = useContext(AuthContext);
  const { colors } = useContext(ThemeContext);
  const { t } = useTranslation();

  const handleLogout = () => {
    Alert.alert(
      t('common.logout'),
      t('common.logout') + '?',
      [
        { text: t('common.no'), style: 'cancel' },
        {
          text: t('common.yes'),
          onPress: async () => {
            await signOut();
            navigation.reset({
              index: 0,
              routes: [{ name: 'Login' }],
            });
          },
        },
      ]
    );
  };

  const styles = createStyles(colors);

  const MenuButton = ({ icon, label, onPress }) => (
    <TouchableOpacity
      style={[styles.menuButton, { backgroundColor: colors.surface, borderColor: colors.border }]}
      onPress={onPress}
    >
      <Text style={styles.menuIcon}>{icon}</Text>
      <Text style={[styles.menuLabel, { color: colors.text }]}>{label}</Text>
      <Text style={[styles.menuArrow, { color: colors.textSecondary }]}>→</Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Profile Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View style={[styles.avatarContainer, { backgroundColor: colors.primary }]}>
          <Text style={styles.avatarText}>
            {user?.first_name?.[0]?.toUpperCase() || 'U'}
          </Text>
        </View>
        <View style={styles.userInfo}>
          <Text style={[styles.userName, { color: colors.text }]}>
            {user?.first_name} {user?.last_name}
          </Text>
          <Text style={[styles.userPhone, { color: colors.textSecondary }]}>
            {user?.phone}
          </Text>
        </View>
        <TouchableOpacity onPress={() => navigation.navigate('EditProfile')}>
          <Text style={[styles.editIcon, { color: colors.primary }]}>✏️</Text>
        </TouchableOpacity>
      </View>

      {/* Menu Items */}
      <View style={styles.menuContainer}>
        <MenuButton
          icon="📋"
          label={t('profile.my_bookings')}
          onPress={() => navigation.navigate('MyBookings')}
        />
        <MenuButton
          icon="❤️"
          label={t('profile.favorites')}
          onPress={() => navigation.navigate('Favorites')}
        />
        <MenuButton
          icon="⚙️"
          label={t('settings.title')}
          onPress={() => navigation.navigate('Settings')}
        />
        <MenuButton
          icon="❓"
          label={t('profile.help')}
          onPress={() => Alert.alert(t('profile.help'), 'Contact support')}
        />
        <MenuButton
          icon="ℹ️"
          label={t('profile.about')}
          onPress={() => Alert.alert(t('profile.about'), 'OLDINDAN v1.0.0')}
        />
      </View>

      {/* Logout Button */}
      <TouchableOpacity
        style={[styles.logoutButton, { backgroundColor: colors.error }]}
        onPress={handleLogout}
      >
        <Text style={styles.logoutButtonText}>{t('common.logout')}</Text>
      </TouchableOpacity>

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
      padding: 16,
      marginBottom: 20,
    },
    avatarContainer: {
      width: 60,
      height: 60,
      borderRadius: 30,
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    avatarText: {
      color: '#fff',
      fontSize: 24,
      fontWeight: 'bold',
    },
    userInfo: {
      flex: 1,
    },
    userName: {
      fontSize: 18,
      fontWeight: 'bold',
      marginBottom: 4,
    },
    userPhone: {
      fontSize: 12,
    },
    editIcon: {
      fontSize: 20,
    },
    menuContainer: {
      paddingHorizontal: 16,
    },
    menuButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 12,
      paddingVertical: 14,
      marginBottom: 8,
      borderRadius: 8,
      borderWidth: 1,
    },
    menuIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    menuLabel: {
      flex: 1,
      fontSize: 14,
      fontWeight: '500',
    },
    menuArrow: {
      fontSize: 16,
    },
    logoutButton: {
      marginHorizontal: 16,
      paddingVertical: 12,
      borderRadius: 8,
      alignItems: 'center',
      marginTop: 20,
    },
    logoutButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
    spacer: {
      height: 40,
    },
  });

export default ProfileScreen;
