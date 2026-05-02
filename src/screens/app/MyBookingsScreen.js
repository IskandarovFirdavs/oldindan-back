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
import { useIsFocused } from '@react-navigation/native';
import { ThemeContext } from '../../context/ThemeContext';
import { bookingAPI } from '../../services/api';

const MyBookingsScreen = ({ navigation }) => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('current');
  const [refreshing, setRefreshing] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);
  const isFocused = useIsFocused();

  useEffect(() => {
    if (isFocused) {
      loadBookings();
    }
  }, [isFocused]);

  const loadBookings = async () => {
    try {
      setLoading(true);
      const response = await bookingAPI.getMyBookings({});
      setBookings(response.data || []);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBookings();
    setRefreshing(false);
  };

  const handleCancelBooking = async (bookingId) => {
    Alert.alert(
      t('booking.cancel_booking'),
      t('booking.cancel_confirmation'),
      [
        { text: t('common.no'), style: 'cancel' },
        {
          text: t('common.yes'),
          onPress: async () => {
            try {
              await bookingAPI.cancelBooking(bookingId, { note: 'Canceled by user' });
              loadBookings();
              Alert.alert(t('common.success'), t('booking.booking_success'));
            } catch (error) {
              Alert.alert(t('errors.error'), t('errors.something_wrong'));
            }
          },
        },
      ]
    );
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed':
        return colors.success;
      case 'canceled':
        return colors.error;
      case 'completed':
        return colors.primary;
      default:
        return colors.warning;
    }
  };

  const filterBookings = () => {
    if (activeTab === 'current') {
      const now = new Date();
      return bookings.filter((b) => new Date(b.booking_start) > now && b.status !== 'canceled');
    }
    return bookings.filter((b) => new Date(b.booking_start) <= new Date() || b.status === 'canceled');
  };

  const styles = createStyles(colors);

  const BookingCard = ({ item }) => (
    <View style={[styles.card, { borderColor: colors.border, backgroundColor: colors.surface }]}>
      <View style={styles.cardHeader}>
        <Text style={[styles.restaurantName, { color: colors.text }]}>
          {item.branch?.brand?.name || item.branch?.name}
        </Text>
        <Text style={[styles.status, { color: getStatusColor(item.status) }]}>
          {item.status}
        </Text>
      </View>

      <Text style={[styles.dateTime, { color: colors.textSecondary }]}>
        {new Date(item.booking_start).toLocaleString()}
      </Text>

      <Text style={[styles.details, { color: colors.textSecondary }]}>
        {item.guest_count} {t('booking.guests')}
      </Text>

      <View style={styles.cardFooter}>
        <TouchableOpacity
          onPress={() => navigation.navigate('BookingDetail', { bookingId: item.id })}
        >
          <Text style={[styles.viewButton, { color: colors.primary }]}>
            {t('common.edit')}
          </Text>
        </TouchableOpacity>

        {item.status === 'pending' && (
          <TouchableOpacity onPress={() => handleCancelBooking(item.id)}>
            <Text style={[styles.cancelButton, { color: colors.error }]}>
              {t('booking.cancel_booking')}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const filteredBookings = filterBookings();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Tabs */}
      <View style={[styles.tabContainer, { borderBottomColor: colors.border }]}>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'current' && [styles.activeTab, { borderBottomColor: colors.primary }],
          ]}
          onPress={() => setActiveTab('current')}
        >
          <Text
            style={[
              styles.tabText,
              { color: activeTab === 'current' ? colors.primary : colors.textSecondary },
            ]}
          >
            {t('booking.title')}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'history' && [styles.activeTab, { borderBottomColor: colors.primary }],
          ]}
          onPress={() => setActiveTab('history')}
        >
          <Text
            style={[
              styles.tabText,
              { color: activeTab === 'history' ? colors.primary : colors.textSecondary },
            ]}
          >
            {t('booking.history')}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Bookings List */}
      {filteredBookings.length > 0 ? (
        <FlatList
          data={filteredBookings}
          renderItem={({ item }) => <BookingCard item={item} />}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        />
      ) : (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
            {activeTab === 'current'
              ? t('booking.my_bookings')
              : t('booking.history')}
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
    tabContainer: {
      flexDirection: 'row',
      borderBottomWidth: 1,
      backgroundColor: colors.surface,
    },
    tab: {
      flex: 1,
      paddingVertical: 12,
      alignItems: 'center',
      borderBottomWidth: 3,
      borderBottomColor: 'transparent',
    },
    activeTab: {
      borderBottomWidth: 3,
    },
    tabText: {
      fontSize: 14,
      fontWeight: '600',
    },
    listContent: {
      padding: 16,
    },
    card: {
      borderWidth: 1,
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
    },
    cardHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 8,
    },
    restaurantName: {
      fontSize: 16,
      fontWeight: '600',
      flex: 1,
    },
    status: {
      fontSize: 12,
      fontWeight: 'bold',
      textTransform: 'capitalize',
    },
    dateTime: {
      fontSize: 12,
      marginBottom: 4,
    },
    details: {
      fontSize: 12,
      marginBottom: 8,
    },
    cardFooter: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: 8,
      paddingTop: 8,
      borderTopWidth: 1,
      borderTopColor: 'rgba(0,0,0,0.1)',
    },
    viewButton: {
      fontSize: 12,
      fontWeight: '600',
    },
    cancelButton: {
      fontSize: 12,
      fontWeight: '600',
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

export default MyBookingsScreen;
