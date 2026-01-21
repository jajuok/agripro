import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import MapView, {
  Marker,
  Polygon,
  PROVIDER_GOOGLE,
  MapPressEvent,
  Region,
  LatLng,
} from 'react-native-maps';
import * as Location from 'expo-location';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { gisApi } from '@/services/api';

type GeoJSONPolygon = {
  type: 'Polygon';
  coordinates: number[][][];
};

type BoundaryMapProps = {
  initialLocation?: {
    latitude: number;
    longitude: number;
  };
  initialBoundary?: GeoJSONPolygon;
  onBoundaryChange?: (boundary: GeoJSONPolygon | null) => void;
  onAreaCalculated?: (areaAcres: number) => void;
  editable?: boolean;
  showControls?: boolean;
};

export const BoundaryMap: React.FC<BoundaryMapProps> = ({
  initialLocation,
  initialBoundary,
  onBoundaryChange,
  onAreaCalculated,
  editable = true,
  showControls = true,
}) => {
  const mapRef = useRef<MapView>(null);
  const [points, setPoints] = useState<LatLng[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isWalking, setIsWalking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [areaAcres, setAreaAcres] = useState<number | null>(null);
  const [currentLocation, setCurrentLocation] = useState<LatLng | null>(null);
  const [region, setRegion] = useState<Region>({
    latitude: initialLocation?.latitude || -1.286389,
    longitude: initialLocation?.longitude || 36.817223,
    latitudeDelta: 0.005,
    longitudeDelta: 0.005,
  });

  const locationSubscription = useRef<Location.LocationSubscription | null>(null);

  // Convert GeoJSON to points
  useEffect(() => {
    if (initialBoundary?.coordinates?.[0]) {
      const coords = initialBoundary.coordinates[0];
      // Remove closing point if it's the same as the first
      const pts = coords.slice(0, -1).map((coord) => ({
        latitude: coord[1],
        longitude: coord[0],
      }));
      setPoints(pts);
    }
  }, [initialBoundary]);

  // Convert points to GeoJSON
  const toGeoJSON = useCallback((pts: LatLng[]): GeoJSONPolygon | null => {
    if (pts.length < 3) return null;

    // Close the polygon
    const coordinates = [
      ...pts.map((p) => [p.longitude, p.latitude]),
      [pts[0].longitude, pts[0].latitude],
    ];

    return {
      type: 'Polygon',
      coordinates: [coordinates],
    };
  }, []);

  // Calculate area when points change
  const calculateArea = useCallback(async (pts: LatLng[]) => {
    if (pts.length < 3) {
      setAreaAcres(null);
      onAreaCalculated?.(0);
      return;
    }

    const geojson = toGeoJSON(pts);
    if (!geojson) return;

    try {
      const result = await gisApi.calculateArea(geojson);
      setAreaAcres(result.area_acres);
      onAreaCalculated?.(result.area_acres);
    } catch (error) {
      console.error('Failed to calculate area:', error);
    }
  }, [toGeoJSON, onAreaCalculated]);

  // Notify parent of boundary changes
  useEffect(() => {
    const geojson = toGeoJSON(points);
    onBoundaryChange?.(geojson);
    if (points.length >= 3) {
      calculateArea(points);
    }
  }, [points, toGeoJSON, onBoundaryChange, calculateArea]);

  // Handle map press to add point
  const handleMapPress = (event: MapPressEvent) => {
    if (!editable || !isDrawing) return;

    const { coordinate } = event.nativeEvent;
    setPoints((prev) => [...prev, coordinate]);
  };

  // Start walk-the-boundary mode
  const startWalking = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Location permission is required to walk the boundary.');
      return;
    }

    setIsWalking(true);
    setPoints([]);

    // Watch position and add points
    locationSubscription.current = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.BestForNavigation,
        distanceInterval: 5, // Add point every 5 meters
      },
      (location) => {
        const newPoint = {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        };
        setCurrentLocation(newPoint);
        setPoints((prev) => [...prev, newPoint]);

        // Center map on current location
        mapRef.current?.animateToRegion({
          ...newPoint,
          latitudeDelta: 0.002,
          longitudeDelta: 0.002,
        });
      }
    );
  };

  // Stop walk-the-boundary mode
  const stopWalking = () => {
    if (locationSubscription.current) {
      locationSubscription.current.remove();
      locationSubscription.current = null;
    }
    setIsWalking(false);
  };

  // Clear all points
  const clearBoundary = () => {
    Alert.alert(
      'Clear Boundary',
      'Are you sure you want to clear the boundary?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            setPoints([]);
            setAreaAcres(null);
            onBoundaryChange?.(null);
          },
        },
      ]
    );
  };

  // Undo last point
  const undoLastPoint = () => {
    if (points.length > 0) {
      setPoints((prev) => prev.slice(0, -1));
    }
  };

  // Get current location
  const goToCurrentLocation = async () => {
    setIsLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required.');
        return;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      const newRegion = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 0.005,
        longitudeDelta: 0.005,
      };

      setRegion(newRegion);
      mapRef.current?.animateToRegion(newRegion);
    } catch (error) {
      Alert.alert('Error', 'Failed to get current location.');
    } finally {
      setIsLoading(false);
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (locationSubscription.current) {
        locationSubscription.current.remove();
      }
    };
  }, []);

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        provider={PROVIDER_GOOGLE}
        initialRegion={region}
        onPress={handleMapPress}
        showsUserLocation
        showsMyLocationButton={false}
        mapType="hybrid"
      >
        {/* Polygon */}
        {points.length >= 3 && (
          <Polygon
            coordinates={points}
            fillColor="rgba(76, 175, 80, 0.3)"
            strokeColor={COLORS.primary}
            strokeWidth={2}
          />
        )}

        {/* Markers for each point */}
        {editable &&
          points.map((point, index) => (
            <Marker
              key={index}
              coordinate={point}
              anchor={{ x: 0.5, y: 0.5 }}
              draggable={editable && !isWalking}
              onDragEnd={(e) => {
                const newPoints = [...points];
                newPoints[index] = e.nativeEvent.coordinate;
                setPoints(newPoints);
              }}
            >
              <View
                style={[
                  styles.marker,
                  index === 0 && styles.markerStart,
                  index === points.length - 1 && styles.markerEnd,
                ]}
              >
                <Text style={styles.markerText}>{index + 1}</Text>
              </View>
            </Marker>
          ))}

        {/* Current location marker when walking */}
        {isWalking && currentLocation && (
          <Marker coordinate={currentLocation}>
            <View style={styles.currentLocationMarker} />
          </Marker>
        )}
      </MapView>

      {/* Area display */}
      {areaAcres !== null && (
        <View style={styles.areaContainer}>
          <Text style={styles.areaLabel}>Calculated Area</Text>
          <Text style={styles.areaValue}>{areaAcres.toFixed(2)} acres</Text>
        </View>
      )}

      {/* Controls */}
      {showControls && editable && (
        <View style={styles.controls}>
          {!isWalking ? (
            <>
              <TouchableOpacity
                style={[styles.controlButton, isDrawing && styles.controlButtonActive]}
                onPress={() => setIsDrawing(!isDrawing)}
              >
                <Text style={[styles.controlText, isDrawing && styles.controlTextActive]}>
                  {isDrawing ? 'Stop Drawing' : 'Tap to Draw'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.controlButton, styles.controlButtonSecondary]}
                onPress={startWalking}
              >
                <Text style={styles.controlText}>Walk Boundary</Text>
              </TouchableOpacity>
            </>
          ) : (
            <TouchableOpacity
              style={[styles.controlButton, styles.controlButtonDanger]}
              onPress={stopWalking}
            >
              <Text style={[styles.controlText, styles.controlTextActive]}>
                Stop Walking ({points.length} points)
              </Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.controlButtonSmall}
            onPress={undoLastPoint}
            disabled={points.length === 0}
          >
            <Text style={[styles.controlTextSmall, points.length === 0 && styles.controlTextDisabled]}>
              Undo
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.controlButtonSmall}
            onPress={clearBoundary}
            disabled={points.length === 0}
          >
            <Text style={[styles.controlTextSmall, points.length === 0 && styles.controlTextDisabled]}>
              Clear
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Location button */}
      <TouchableOpacity style={styles.locationButton} onPress={goToCurrentLocation}>
        {isLoading ? (
          <ActivityIndicator size="small" color={COLORS.primary} />
        ) : (
          <Text style={styles.locationButtonText}>📍</Text>
        )}
      </TouchableOpacity>

      {/* Instructions */}
      {editable && isDrawing && points.length < 3 && (
        <View style={styles.instructions}>
          <Text style={styles.instructionText}>
            Tap on the map to add points. Add at least 3 points to create a boundary.
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
  },
  map: {
    flex: 1,
  },
  areaContainer: {
    position: 'absolute',
    top: SPACING.md,
    left: SPACING.md,
    backgroundColor: COLORS.white,
    padding: SPACING.sm,
    borderRadius: 8,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  areaLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[600],
  },
  areaValue: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  controls: {
    position: 'absolute',
    bottom: SPACING.lg,
    left: SPACING.md,
    right: SPACING.md,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  controlButton: {
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: 8,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  controlButtonActive: {
    backgroundColor: COLORS.primary,
  },
  controlButtonSecondary: {
    backgroundColor: COLORS.info,
  },
  controlButtonDanger: {
    backgroundColor: COLORS.error,
  },
  controlText: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[800],
  },
  controlTextActive: {
    color: COLORS.white,
  },
  controlButtonSmall: {
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.sm,
    borderRadius: 6,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  controlTextSmall: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[700],
  },
  controlTextDisabled: {
    color: COLORS.gray[400],
  },
  locationButton: {
    position: 'absolute',
    top: SPACING.md,
    right: SPACING.md,
    backgroundColor: COLORS.white,
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  locationButtonText: {
    fontSize: 20,
  },
  marker: {
    backgroundColor: COLORS.primary,
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  markerStart: {
    backgroundColor: COLORS.success,
  },
  markerEnd: {
    backgroundColor: COLORS.secondary,
  },
  markerText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.xs,
    fontWeight: 'bold',
  },
  currentLocationMarker: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.info,
    borderWidth: 3,
    borderColor: COLORS.white,
  },
  instructions: {
    position: 'absolute',
    bottom: 120,
    left: SPACING.md,
    right: SPACING.md,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: SPACING.sm,
    borderRadius: 8,
  },
  instructionText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.sm,
    textAlign: 'center',
  },
});

export default BoundaryMap;
