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
import DateTimePicker from 'react-native-date-picker';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { bookingAPI } from '../../services/api';

const BookingFormScreen = ({ route, navigation }) => {
  const { branchId } = route.params;
  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [guests, setGuests] = useState('2');
  const [children, setChildren] = useState('0');
  const [specialRequest, setSpecialRequest] = useState('');
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  const handleBooking = async () => {
    if (!guests.trim() || parseInt(guests) < 1) {
      Alert.alert(t('errors.error'), t('errors.required_field'));
      return;
    }

    setLoading(true);
    try {
      // Calculate end time (1 hour by default)
      const endTime = new Date(date);
      endTime.setHours(endTime.getHours() + 1);

      const response = await bookingAPI.createBooking({
        branch_id: branchId,
        booking_start: date.toISOString(),
        booking_end: endTime.toISOString(),
        guest_count: parseInt(guests),
        children_count: parseInt(children) || 0,
        special_request: specialRequest,
      });

      Alert.alert(
        t('common.success'),
        t('booking.booking_success'),
        [
          {
            text: 'OK',
            onPress: () => {
              navigation.navigate('MyBookings');
            },
          },
        ]
      );
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
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.text }]}>{t('booking.book_table')}</Text>
      </View>

      <View style={styles.formContainer}>
        {/* Date & Time */}
        <Text style={[styles.label, { color: colors.text }]}>
          {t('booking.date_time')}
        </Text>
        <TouchableOpacity
          style={[styles.input, { borderColor: colors.border, backgroundColor: colors.surface }]}
          onPress={() => setShowDatePicker(true)}
        >
          <Text style={[{ color: colors.text }, styles.dateText]}>
            {date.toLocaleString()}
          </Text>
        </TouchableOpacity>

        <DateTimePicker
          modal
          open={showDatePicker}
          date={date}
          onConfirm={(selectedDate) => {
            setDate(selectedDate);
            setShowDatePicker(false);
          }}
          onCancel={() => {
            setShowDatePicker(false);
          }}
          mode="datetime"
          minimumDate={new Date()}
        />

        {/* Guests */}
        <Text style={[styles.label, { color: colors.text }, { marginTop: 16 }]}>
          {t('booking.guests')}
        </Text>
        <TextInput
          style={[styles.input, { borderColor: colors.border, color: colors.text }]}
          placeholder={t('booking.guests')}
          placeholderTextColor={colors.textSecondary}
          value={guests}
          onChangeText={setGuests}
          keyboardType="numeric"
          editable={!loading}
        />

        {/* Children */}
        <Text style={[styles.label, { color: colors.text }, { marginTop: 16 }]}>
          {t('booking.children')}
        </Text>
        <TextInput
          style={[styles.input, { borderColor: colors.border, color: colors.text }]}
          placeholder={t('booking.children')}
          placeholderTextColor={colors.textSecondary}
          value={children}
          onChangeText={setChildren}
          keyboardType="numeric"
          editable={!loading}
        />

        {/* Special Request */}
        <Text style={[styles.label, { color: colors.text }, { marginTop: 16 }]}>
          {t('booking.special_request')}
        </Text>
        <TextInput
          style={[styles.input, styles.textArea, { borderColor: colors.border, color: colors.text }]}
          placeholder={t('booking.special_request')}
          placeholderTextColor={colors.textSecondary}
          value={specialRequest}
          onChangeText={setSpecialRequest}
          multiline
          numberOfLines={4}
          editable={!loading}
        />

        {/* Confirm Button */}
        <TouchableOpacity
          style={[styles.button, { backgroundColor: colors.primary }]}
          onPress={handleBooking}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>{t('booking.confirm')}</Text>
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
      paddingBottom: 40,
    },
    label: {
      fontSize: 14,
      fontWeight: '600',
      marginBottom: 8,
    },
    input: {
      borderWidth: 1,
      borderRadius: 8,
      paddingHorizontal: 16,
      paddingVertical: 12,
      fontSize: 16,
    },
    dateText: {
      fontSize: 16,
      paddingVertical: 12,
    },
    textArea: {
      minHeight: 100,
      textAlignVertical: 'top',
      paddingTop: 12,
    },
    button: {
      borderRadius: 8,
      paddingVertical: 14,
      alignItems: 'center',
      marginTop: 20,
    },
    buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
  });

export default BookingFormScreen;
