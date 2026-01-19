import { useState, useEffect } from 'react';
import * as Location from 'expo-location';

type LocationState = {
  latitude: number;
  longitude: number;
  accuracy: number | null;
} | null;

export function useLocation() {
  const [location, setLocation] = useState<LocationState>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const requestPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    return status === 'granted';
  };

  const getCurrentLocation = async () => {
    setLoading(true);
    setError(null);

    try {
      const hasPermission = await requestPermission();
      if (!hasPermission) {
        setError('Location permission denied');
        setLoading(false);
        return null;
      }

      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      const locationData = {
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
        accuracy: currentLocation.coords.accuracy,
      };

      setLocation(locationData);
      setLoading(false);
      return locationData;
    } catch (err) {
      setError('Failed to get location');
      setLoading(false);
      return null;
    }
  };

  const watchLocation = async (callback: (location: LocationState) => void) => {
    const hasPermission = await requestPermission();
    if (!hasPermission) {
      setError('Location permission denied');
      return null;
    }

    const subscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 5000,
        distanceInterval: 10,
      },
      (newLocation) => {
        const locationData = {
          latitude: newLocation.coords.latitude,
          longitude: newLocation.coords.longitude,
          accuracy: newLocation.coords.accuracy,
        };
        setLocation(locationData);
        callback(locationData);
      }
    );

    return subscription;
  };

  return {
    location,
    error,
    loading,
    getCurrentLocation,
    watchLocation,
  };
}
