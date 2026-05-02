import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import * as Location from 'expo-location';
import { useTranslation } from 'react-i18next';
import { ThemeContext } from '../../context/ThemeContext';
import { restaurantAPI } from '../../services/api';

const HomeScreen = ({ navigation }) => {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [location, setLocation] = useState(null);
  const [region, setRegion] = useState({
    latitude: 41.2995,
    longitude: 69.2401,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421,
  });
  const [refreshing, setRefreshing] = useState(false);
  const { t } = useTranslation();
  const { colors } = useContext(ThemeContext);

  useEffect(() => {
    requestLocation();
    loadBranches();
  }, []);

  const requestLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const location = await Location.getCurrentPositionAsync({});
        setLocation(location.coords);
        setRegion({
          ...region,
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        });
      }
    } catch (error) {
      console.log('Location error:', error);
    }
  };

  const loadBranches = async () => {
    try {
      setLoading(true);
      const response = await restaurantAPI.getBranches({});
      setBranches(response.data || []);
    } catch (error) {
      Alert.alert(t('errors.error'), t('errors.something_wrong'));
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBranches();
    setRefreshing(false);
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
        {item.latitude && item.longitude && (
          <Text style={[styles.distance, { color: colors.primary }]}>
            {location && `${Math.round(getDistance(location, item))} km away`}
          </Text>
        )}
      </View>
    </TouchableOpacity>
  );

  const getDistance = (loc1, loc2) => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = ((loc2.latitude - loc1.latitude) * Math.PI) / 180;
    const dLon = ((loc2.longitude - loc1.longitude) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((loc1.latitude * Math.PI) / 180) *
      Math.cos((loc2.latitude * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.openDrawer()}>
          <Text style={[styles.menuIcon, { color: colors.primary }]}>☰</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]}>{t('home.title')}</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Notifications')}>
          <Text style={[styles.bellIcon, { color: colors.primary }]}>🔔</Text>
        </TouchableOpacity>
      </View>

      {/* Map */}
      <View style={styles.mapContainer}>
        <MapView style={styles.map} region={region}>
          {location && (
            <Marker coordinate={location} title="You" pinColor={colors.primary} />
          )}
          {branches.map((branch) => (
            branch.latitude && branch.longitude && (
              <Marker
                key={branch.id}
                coordinate={{ latitude: branch.latitude, longitude: branch.longitude }}
                title={branch.name || branch.brand?.name}
                onPress={() => navigation.navigate('RestaurantDetail', { branchId: branch.id })}
              />
            )
          ))}
        </MapView>
      </View>

      {/* Recommended Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          {t('home.recommended')}
        </Text>
        <FlatList
          data={branches.slice(0, 5)}
          renderItem={({ item }) => <RestaurantCard item={item} />}
          keyExtractor={(item) => item.id.toString()}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        />
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
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      backgroundColor: colors.surface,
    },
    menuIcon: {
      fontSize: 24,
    },
    headerTitle: {
      fontSize: 18,
      fontWeight: 'bold',
    },
    bellIcon: {
      fontSize: 20,
    },
    mapContainer: {
      height: 250,
      marginHorizontal: 16,
      marginVertical: 12,
      borderRadius: 12,
      overflow: 'hidden',
    },
    map: {
      flex: 1,
    },
    section: {
      paddingHorizontal: 16,
      marginBottom: 20,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      marginBottom: 12,
    },
    card: {
      borderWidth: 1,
      borderRadius: 8,
      padding: 12,
      marginBottom: 8,
    },
    restaurantName: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 4,
    },
    address: {
      fontSize: 12,
      marginBottom: 4,
    },
    distance: {
      fontSize: 12,
      fontWeight: '500',
    },
  });

export default HomeScreen;
