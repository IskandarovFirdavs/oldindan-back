import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { notificationAPI } from '../../services/api';

const NotificationsScreen = ({ navigation }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationAPI.getNotifications({});
      setNotifications(response.data || []);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNotifications();
    setRefreshing(false);
  };

  const handleMarkAsRead = async (notificationId, isRead) => {
    if (!isRead) {
      try {
        await notificationAPI.markAsRead(notificationId);
        loadNotifications();
      } catch (error) {
        Alert.alert(t('errors.error'), t('errors.something_wrong'));
      }
    }
  };

  const styles = createStyles(colors);

  const NotificationCard = ({ item }) => (
    <TouchableOpacity
      onPress={() => handleMarkAsRead(item.id, item.is_read)}
      style={[
        styles.card,
        { borderColor: colors.border, backgroundColor: colors.surface },
        !item.is_read && { borderLeftWidth: 4, borderLeftColor: colors.primary },
      ]}
    >
      <View style={styles.cardContent}>
        <View style={styles.titleRow}>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>
            {item.title}
          </Text>
          {!item.is_read && (
            <View style={[styles.badge, { backgroundColor: colors.primary }]}>
              <Text style={styles.badgeText}>●</Text>
            </View>
          )}
        </View>
        <Text style={[styles.body, { color: colors.textSecondary }]} numberOfLines={2}>
          {item.body}
        </Text>
        <Text style={[styles.timestamp, { color: colors.textSecondary }]}>
          {new Date(item.created_at).toLocaleString()}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface, borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>{t('notifications.title')}</Text>
      </View>

      {/* Notifications List */}
      {notifications.length > 0 ? (
        <FlatList
          data={notifications}
          renderItem={({ item }) => <NotificationCard item={item} />}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        />
      ) : (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
            {t('notifications.no_notifications')}
          </Text>
        </View>
      )}
    </View>
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
    },
    backButton: {
      fontSize: 14,
      marginRight: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: 'bold',
    },
    listContent: {
      padding: 12,
    },
    card: {
      borderWidth: 1,
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
    },
    cardContent: {
      flex: 1,
    },
    titleRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 6,
    },
    body: {
      fontSize: 13,
      marginBottom: 6,
      lineHeight: 18,
    },
    timestamp: {
      fontSize: 11,
    },
    badge: {
      width: 6,
      height: 6,
      borderRadius: 3,
      marginLeft: 8,
    },
    badgeText: {
      fontSize: 8,
      color: '#fff',
    },
    emptyState: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    emptyText: {
      fontSize: 16,
      textAlign: 'center',
    },
  });

export default NotificationsScreen;
