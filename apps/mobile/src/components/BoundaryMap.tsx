import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { WebView } from 'react-native-webview';
import * as Location from 'expo-location';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { gisApi } from '@/services/api';

type LatLng = { latitude: number; longitude: number };

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

const buildLeafletHTML = (lat: number, lng: number) => {
  return `<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #map { width: 100%; height: 100%; overflow: hidden; }
#loading { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex;
  align-items: center; justify-content: center; background: #f5f5f5; z-index: 9999;
  font-family: sans-serif; color: #666; flex-direction: column; }
#loading.hidden { display: none; }
.marker-label { background: transparent !important; border: none !important;
  box-shadow: none !important; color: #fff !important; font-weight: bold !important;
  font-size: 11px !important; }
</style>
</head>
<body>
<div id="loading"><div style="font-size:32px;margin-bottom:8px">&#x1F5FA;&#xFE0F;</div><div>Loading map...</div></div>
<div id="map"></div>
<script>
// Message handler defined BEFORE Leaflet loads so injectJavaScript always works
var messageQueue = [];
var mapReady = false;
var drawingEnabled = false;
var map, osmLayer, satelliteLayer, currentLayer, markers, polygon, currentLocMarker;

function handleMessage(data) {
  try {
    var msg = typeof data === 'string' ? JSON.parse(data) : data;
    if (!mapReady) { messageQueue.push(msg); return; }
    processMessage(msg);
  } catch(e) {
    window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'error', message: 'handleMessage: ' + e.message }));
  }
}

function processMessage(msg) {
  switch(msg.type) {
    case 'setCenter':
      map.setView([msg.lat, msg.lng], msg.zoom || 17);
      break;
    case 'setPoints':
      updateMap(msg.points);
      break;
    case 'setDrawingEnabled':
      drawingEnabled = msg.enabled;
      break;
    case 'showCurrentLocation':
      showCurrentLocation(msg.lat, msg.lng);
      break;
    case 'toggleSatellite':
      if (currentLayer === 'street') {
        map.removeLayer(osmLayer); satelliteLayer.addTo(map); currentLayer = 'satellite';
      } else {
        map.removeLayer(satelliteLayer); osmLayer.addTo(map); currentLayer = 'street';
      }
      break;
  }
}

function updateMap(pts) {
  markers.forEach(function(m) { map.removeLayer(m); });
  markers = [];
  if (polygon) { map.removeLayer(polygon); polygon = null; }
  pts.forEach(function(p, i) {
    var color = '#2E7D32';
    if (i === 0) color = '#4CAF50';
    else if (i === pts.length - 1) color = '#FF9800';
    var m = L.circleMarker([p.lat, p.lng], {
      radius: 14, fillColor: color, color: '#fff', weight: 2, fillOpacity: 1
    }).addTo(map);
    m.bindTooltip(String(i + 1), { permanent: true, direction: 'center', className: 'marker-label' });
    markers.push(m);
  });
  if (pts.length >= 3) {
    polygon = L.polygon(pts.map(function(p) { return [p.lat, p.lng]; }), {
      color: '#2E7D32', fillColor: 'rgba(76, 175, 80, 0.3)', weight: 2
    }).addTo(map);
  }
}

function showCurrentLocation(lat, lng) {
  if (currentLocMarker) map.removeLayer(currentLocMarker);
  currentLocMarker = L.circleMarker([lat, lng], {
    radius: 8, fillColor: '#2196F3', color: '#fff', weight: 3, fillOpacity: 1
  }).addTo(map);
}

function initMap() {
  try {
    markers = [];
    polygon = null;
    currentLocMarker = null;
    currentLayer = 'street';

    map = L.map('map', { zoomControl: false, attributionControl: false }).setView([${lat}, ${lng}], 17);
    osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 20 }).addTo(map);
    satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 20 });

    map.on('click', function(e) {
      if (!drawingEnabled) return;
      window.ReactNativeWebView.postMessage(JSON.stringify({
        type: 'mapClick', lat: e.latlng.lat, lng: e.latlng.lng
      }));
    });

    document.getElementById('loading').className = 'hidden';
    mapReady = true;

    // Process queued messages
    messageQueue.forEach(function(msg) { processMessage(msg); });
    messageQueue = [];

    window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ready' }));
  } catch(e) {
    document.getElementById('loading').innerHTML = '<div>Map failed to load</div><div style="font-size:12px;color:#999;margin-top:4px">' + e.message + '</div>';
    window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'error', message: 'initMap: ' + e.message }));
  }
}

// Load Leaflet dynamically
var link = document.createElement('link');
link.rel = 'stylesheet';
link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
document.head.appendChild(link);

var script = document.createElement('script');
script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
script.onload = function() { initMap(); };
script.onerror = function() {
  document.getElementById('loading').innerHTML = '<div>Failed to load map library</div><div style="font-size:12px;color:#999;margin-top:4px">Check internet connection</div>';
  window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'error', message: 'Failed to load Leaflet from CDN' }));
};
document.head.appendChild(script);
</script>
</body>
</html>`;
};

export const BoundaryMap: React.FC<BoundaryMapProps> = ({
  initialLocation,
  initialBoundary,
  onBoundaryChange,
  onAreaCalculated,
  editable = true,
  showControls = true,
}) => {
  const webViewRef = useRef<WebView>(null);
  const [points, setPoints] = useState<LatLng[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isWalking, setIsWalking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [areaAcres, setAreaAcres] = useState<number | null>(null);

  const locationSubscription = useRef<Location.LocationSubscription | null>(null);

  // Store callbacks in refs to avoid them triggering effects
  const onBoundaryChangeRef = useRef(onBoundaryChange);
  const onAreaCalculatedRef = useRef(onAreaCalculated);
  onBoundaryChangeRef.current = onBoundaryChange;
  onAreaCalculatedRef.current = onAreaCalculated;

  const centerLat = initialLocation?.latitude || -1.286389;
  const centerLng = initialLocation?.longitude || 36.817223;

  const sendToMap = useCallback((msg: object) => {
    if (!webViewRef.current) return;
    const json = JSON.stringify(msg);
    const escaped = json.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    webViewRef.current.injectJavaScript(`handleMessage('${escaped}'); true;`);
  }, []);

  // Send points to WebView whenever they change
  useEffect(() => {
    sendToMap({
      type: 'setPoints',
      points: points.map((p) => ({ lat: p.latitude, lng: p.longitude })),
    });
  }, [points, sendToMap]);

  // Sync drawing mode to WebView
  useEffect(() => {
    sendToMap({ type: 'setDrawingEnabled', enabled: isDrawing && editable });
  }, [isDrawing, editable, sendToMap]);

  // Load initial boundary
  useEffect(() => {
    if (initialBoundary?.coordinates?.[0]) {
      const coords = initialBoundary.coordinates[0];
      const pts = coords.slice(0, -1).map((coord) => ({
        latitude: coord[1],
        longitude: coord[0],
      }));
      setPoints(pts);
    }
  }, [initialBoundary]);

  // Convert points to GeoJSON (pure function, no deps)
  const toGeoJSON = useCallback((pts: LatLng[]): GeoJSONPolygon | null => {
    if (pts.length < 3) return null;
    const coordinates = [
      ...pts.map((p) => [p.longitude, p.latitude]),
      [pts[0].longitude, pts[0].latitude],
    ];
    return { type: 'Polygon', coordinates: [coordinates] };
  }, []);

  // Notify parent and calculate area when points change
  // Uses refs for callbacks to avoid infinite re-render loops
  useEffect(() => {
    const geojson = toGeoJSON(points);
    onBoundaryChangeRef.current?.(geojson);

    if (points.length >= 3 && geojson) {
      gisApi.calculateArea(geojson).then((result) => {
        setAreaAcres(result.area_acres);
        onAreaCalculatedRef.current?.(result.area_acres);
      }).catch((error) => {
        console.error('Failed to calculate area:', error);
      });
    } else {
      setAreaAcres(null);
    }
  }, [points, toGeoJSON]);

  // Handle messages from WebView
  const handleWebViewMessage = useCallback((event: { nativeEvent: { data: string } }) => {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg.type === 'ready') {
        setMapReady(true);
        setMapError(null);
      } else if (msg.type === 'mapClick') {
        setPoints((prev) => [...prev, { latitude: msg.lat, longitude: msg.lng }]);
      } else if (msg.type === 'error') {
        console.warn('BoundaryMap WebView error:', msg.message);
        setMapError(msg.message);
      }
    } catch {}
  }, []);

  // Start walk-the-boundary mode
  const startWalking = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Location permission is required to walk the boundary.');
      return;
    }
    setIsWalking(true);
    setPoints([]);

    locationSubscription.current = await Location.watchPositionAsync(
      { accuracy: Location.Accuracy.BestForNavigation, distanceInterval: 5 },
      (location) => {
        const newPoint = {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        };
        setPoints((prev) => [...prev, newPoint]);
        sendToMap({ type: 'showCurrentLocation', lat: newPoint.latitude, lng: newPoint.longitude });
        sendToMap({ type: 'setCenter', lat: newPoint.latitude, lng: newPoint.longitude, zoom: 18 });
      }
    );
  };

  const stopWalking = () => {
    if (locationSubscription.current) {
      locationSubscription.current.remove();
      locationSubscription.current = null;
    }
    setIsWalking(false);
  };

  const clearBoundary = () => {
    Alert.alert('Clear Boundary', 'Are you sure you want to clear the boundary?', [
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
    ]);
  };

  const undoLastPoint = () => {
    if (points.length > 0) {
      setPoints((prev) => prev.slice(0, -1));
    }
  };

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
      sendToMap({
        type: 'setCenter',
        lat: location.coords.latitude,
        lng: location.coords.longitude,
        zoom: 17,
      });
    } catch {
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
      <WebView
        ref={webViewRef}
        source={{ html: buildLeafletHTML(centerLat, centerLng), baseUrl: 'https://unpkg.com' }}
        style={styles.map}
        onMessage={handleWebViewMessage}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        mixedContentMode="always"
        allowFileAccess={true}
        originWhitelist={['*']}
        scrollEnabled={false}
        bounces={false}
        overScrollMode="never"
        startInLoadingState={false}
        cacheEnabled={true}
        onError={(e) => {
          console.warn('WebView error:', e.nativeEvent);
          setMapError('WebView failed to load');
        }}
      />

      {/* Error overlay */}
      {mapError && (
        <View style={styles.errorOverlay}>
          <Text style={styles.errorText}>{mapError}</Text>
        </View>
      )}

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
                <Text style={[styles.controlText, styles.controlTextActive]}>Walk Boundary</Text>
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

          <TouchableOpacity
            style={styles.controlButtonSmall}
            onPress={() => sendToMap({ type: 'toggleSatellite' })}
          >
            <Text style={styles.controlTextSmall}>Satellite</Text>
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
  errorOverlay: {
    position: 'absolute',
    top: SPACING.md,
    left: SPACING.md,
    right: SPACING.md,
    backgroundColor: '#FFF3E0',
    padding: SPACING.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFB74D',
  },
  errorText: {
    fontSize: FONT_SIZES.xs,
    color: '#E65100',
    textAlign: 'center',
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
