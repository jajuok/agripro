import { useState } from 'react';
import { Platform } from 'react-native';

type LocationState = {
  latitude: number;
  longitude: number;
  accuracy: number | null;
} | null;

export function useLocation() {
  const [location, setLocation] = useState<LocationState>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const getCurrentLocation = async () => {
    setLoading(true);
    setError(null);

    try {
      if (Platform.OS === 'web') {
        return await new Promise<LocationState>((resolve) => {
          if (!navigator.geolocation) {
            setError('Geolocation not supported');
            setLoading(false);
            resolve(null);
            return;
          }
          navigator.geolocation.getCurrentPosition(
            (position) => {
              const locationData = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
              };
              setLocation(locationData);
              setLoading(false);
              resolve(locationData);
            },
            (err) => {
              setError(err.message || 'Failed to get location');
              setLoading(false);
              resolve(null);
            },
            { enableHighAccuracy: true, timeout: 15000 }
          );
        });
      }

      // Native path
      const Location = require('expo-location');
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
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
    if (Platform.OS === 'web') {
      if (!navigator.geolocation) {
        setError('Geolocation not supported');
        return null;
      }
      const watchId = navigator.geolocation.watchPosition(
        (position) => {
          const locationData = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          };
          setLocation(locationData);
          callback(locationData);
        },
        (err) => {
          setError(err.message || 'Failed to watch location');
        },
        { enableHighAccuracy: true, timeout: 15000 }
      );
      // Return an object with .remove() to match expo-location subscription API
      return { remove: () => navigator.geolocation.clearWatch(watchId) };
    }

    // Native path
    const Location = require('expo-location');
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      setError('Location permission denied');
      return null;
    }

    const subscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 5000,
        distanceInterval: 10,
      },
      (newLocation: any) => {
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
