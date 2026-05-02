import React, { useState, useContext } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { restaurantAPI } from '../../services/api';

const SearchScreen = ({ navigation }) => {
  const [searchText, setSearchText] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  const handleSearch = async (text) => {
    setSearchText(text);

    if (!text.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await restaurantAPI.searchBranches(text);
      setResults(response.data || []);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const styles = createStyles(colors);

  const RestaurantCard = ({ item }) => (
    <TouchableOpacity
      style={[styles.card, { borderColor: colors.border, backgroundColor: colors.surface }]}
      onPress={() => navigation.navigate('RestaurantDetail', { branchId: item.id })}
    >
      <View>
        <Text style={[styles.restaurantName, { color: colors.text }]}>
          {item.brand?.name || item.name}
        </Text>
        <Text style={[styles.address, { color: colors.textSecondary }]} numberOfLines={1}>
          {item.address}
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.backButton, { color: colors.primary }]}>←</Text>
        </TouchableOpacity>
        <TextInput
          style={[styles.searchInput, { borderColor: colors.border, color: colors.text }]}
          placeholder={t('search.search_placeholder')}
          placeholderTextColor={colors.textSecondary}
          value={searchText}
          onChangeText={handleSearch}
          autoFocus
        />
      </View>

      {/* Results */}
      {loading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : results.length > 0 ? (
        <FlatList
          data={results}
          renderItem={({ item }) => <RestaurantCard item={item} />}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
        />
      ) : searchText.trim() ? (
        <View style={styles.centerContent}>
          <Text style={[styles.noResults, { color: colors.textSecondary }]}>
            {t('search.no_results')}
          </Text>
        </View>
      ) : (
        <View style={styles.centerContent}>
          <Text style={[styles.placeholder, { color: colors.textSecondary }]}>
            {t('search.search_placeholder')}
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
      paddingHorizontal: 12,
      paddingVertical: 12,
      backgroundColor: colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    backButton: {
      fontSize: 24,
      marginRight: 12,
    },
    searchInput: {
      flex: 1,
      borderWidth: 1,
      borderRadius: 20,
      paddingHorizontal: 16,
      paddingVertical: 8,
      fontSize: 14,
    },
    centerContent: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
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
    restaurantName: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 4,
    },
    address: {
      fontSize: 12,
    },
    noResults: {
      fontSize: 16,
      textAlign: 'center',
    },
    placeholder: {
      fontSize: 16,
      textAlign: 'center',
    },
  });

export default SearchScreen;
