import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { bookingAPI } from '../../services/api';

const BookingDetailScreen = ({ route, navigation }) => {
  const { bookingId } = route.params;
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  useEffect(() => {
    loadBookingDetail();
  }, [bookingId]);

  const loadBookingDetail = async () => {
    try {
      setLoading(true);
      const response = await bookingAPI.getBookingDetail(bookingId);
      setBooking(response.data);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = () => {
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
              Alert.alert(t('common.success'), t('booking.booking_success'));
              navigation.goBack();
            } catch (error) {
              Alert.alert(t('errors.error'), t('errors.something_wrong'));
            }
          },
        },
      ]
    );
  };

  const styles = createStyles(colors);

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!booking) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={[styles.errorText, { color: colors.error }]}>
          {t('errors.something_wrong')}
        </Text>
      </View>
    );
  }

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

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>{t('booking.title')}</Text>
      </View>

      {/* Booking Info */}
      <View style={[styles.infoContainer, { backgroundColor: colors.surface }]}>
        <View style={styles.statusRow}>
          <Text style={[styles.label, { color: colors.textSecondary }]}>
            {t('common.status')}
          </Text>
          <Text style={[styles.status, { color: getStatusColor(booking.status) }]}>
            {booking.status}
          </Text>
        </View>

        <Text style={[styles.restaurantName, { color: colors.text }]}>
          {booking.branch?.brand?.name || booking.branch?.name}
        </Text>

        <Text style={[styles.address, { color: colors.textSecondary }]}>
          {booking.branch?.address}
        </Text>
      </View>

      {/* Details */}
      <View style={styles.detailsContainer}>
        <DetailRow
          label={t('booking.date_time')}
          value={new Date(booking.booking_start).toLocaleString()}
          colors={colors}
        />

        <DetailRow
          label="End Time"
          value={new Date(booking.booking_end).toLocaleString()}
          colors={colors}
        />

        <DetailRow
          label={t('booking.guests')}
          value={`${booking.guest_count} guests`}
          colors={colors}
        />

        {booking.children_count > 0 && (
          <DetailRow
            label={t('booking.children')}
            value={`${booking.children_count} children`}
            colors={colors}
          />
        )}

        {booking.special_request && (
          <View style={[styles.detailRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
              {t('booking.special_request')}
            </Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>
              {booking.special_request}
            </Text>
          </View>
        )}

        {booking.status === 'pending' && (
          <TouchableOpacity
            style={[styles.cancelButton, { backgroundColor: colors.error }]}
            onPress={handleCancelBooking}
          >
            <Text style={styles.cancelButtonText}>{t('booking.cancel_booking')}</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
};

const DetailRow = ({ label, value, colors }) => (
  <View style={[styles.detailRow, { borderBottomColor: colors.border }]}>
    <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
      {label}
    </Text>
    <Text style={[styles.detailValue, { color: colors.text }]}>
      {value}
    </Text>
  </View>
);

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
    infoContainer: {
      paddingHorizontal: 16,
      paddingVertical: 16,
      marginVertical: 12,
    },
    statusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    label: {
      fontSize: 12,
    },
    status: {
      fontSize: 14,
      fontWeight: 'bold',
      textTransform: 'capitalize',
    },
    restaurantName: {
      fontSize: 20,
      fontWeight: 'bold',
      marginBottom: 4,
    },
    address: {
      fontSize: 14,
    },
    detailsContainer: {
      paddingHorizontal: 16,
      paddingBottom: 20,
    },
    detailRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 12,
      borderBottomWidth: 1,
    },
    detailLabel: {
      fontSize: 14,
    },
    detailValue: {
      fontSize: 14,
      fontWeight: '600',
    },
    errorText: {
      fontSize: 16,
    },
    cancelButton: {
      marginTop: 20,
      borderRadius: 8,
      paddingVertical: 12,
      alignItems: 'center',
    },
    cancelButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
  });

export default BookingDetailScreen;
