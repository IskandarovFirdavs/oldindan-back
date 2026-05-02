import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { restaurantAPI, favoriteAPI } from '../../services/api';

const RestaurantDetailScreen = ({ route, navigation }) => {
  const { branchId } = route.params;
  const [branch, setBranch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  useEffect(() => {
    loadBranchDetail();
  }, [branchId]);

  const loadBranchDetail = async () => {
    try {
      setLoading(true);
      const response = await restaurantAPI.getBranchDetail(branchId);
      setBranch(response.data);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async () => {
    try {
      if (isFavorite) {
        await favoriteAPI.removeFavorite(branchId);
      } else {
        await favoriteAPI.addFavorite(branchId);
      }
      setIsFavorite(!isFavorite);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    }
  };

  const handleCall = () => {
    if (branch?.phone) {
      Linking.openURL(`tel:${branch.phone}`);
    }
  };

  const styles = createStyles(colors);

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!branch) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={[styles.errorText, { color: colors.error }]}>
          {t('errors.something_wrong')}
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.text }]}>← {t('common.back')}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={toggleFavorite}>
          <Text style={[styles.favoriteButton, { color: colors.primary }]}>
            {isFavorite ? '❤️' : '🤍'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Restaurant Info */}
      <View style={[styles.infoContainer, { backgroundColor: colors.surface }]}>
        <Text style={[styles.title, { color: colors.text }]}>
          {branch.brand?.name || branch.name}
        </Text>
        <Text style={[styles.address, { color: colors.textSecondary }]}>
          {branch.address}
        </Text>

        {branch.phone && (
          <TouchableOpacity
            onPress={handleCall}
            style={[styles.phoneButton, { backgroundColor: colors.primary }]}
          >
            <Text style={styles.phoneButtonText}>{t('restaurant.call')}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Details */}
      <View style={styles.detailsContainer}>
        <View style={[styles.detailRow, { borderBottomColor: colors.border }]}>
          <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
            {t('restaurant.working_hours')}
          </Text>
          <Text style={[styles.detailValue, { color: colors.text }]}>
            {branch.working_hours_json ? '24/7' : 'Check details'}
          </Text>
        </View>

        {branch.service_fee > 0 && (
          <View style={[styles.detailRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
              Service Fee
            </Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>
              {branch.service_fee} so'm
            </Text>
          </View>
        )}

        {branch.deposit_enabled && (
          <View style={[styles.detailRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
              Deposit
            </Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>
              {branch.deposit_amount} so'm
            </Text>
          </View>
        )}
      </View>

      {/* Book Button */}
      <TouchableOpacity
        style={[styles.bookButton, { backgroundColor: colors.primary }]}
        onPress={() => navigation.navigate('BookingForm', { branchId })}
      >
        <Text style={styles.bookButtonText}>{t('restaurant.book_table')}</Text>
      </TouchableOpacity>
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
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      backgroundColor: colors.surface,
    },
    backButton: {
      fontSize: 14,
    },
    favoriteButton: {
      fontSize: 24,
    },
    infoContainer: {
      paddingHorizontal: 16,
      paddingVertical: 20,
      marginVertical: 12,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      marginBottom: 8,
    },
    address: {
      fontSize: 14,
      marginBottom: 16,
    },
    phoneButton: {
      borderRadius: 8,
      paddingVertical: 10,
      alignItems: 'center',
      marginTop: 10,
    },
    phoneButtonText: {
      color: '#fff',
      fontSize: 14,
      fontWeight: '600',
    },
    detailsContainer: {
      paddingHorizontal: 16,
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
    bookButton: {
      margin: 16,
      borderRadius: 8,
      paddingVertical: 14,
      alignItems: 'center',
      marginTop: 20,
    },
    bookButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
    },
    errorText: {
      fontSize: 16,
    },
  });

export default RestaurantDetailScreen;
