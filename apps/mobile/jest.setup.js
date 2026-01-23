/* eslint-disable @typescript-eslint/no-require-imports */
/**
 * Jest Setup File
 * Configures test environment, mocks, and global test utilities
 */

import '@testing-library/jest-native/extend-expect';

// Polyfill for setImmediate (used by React Native's InteractionManager)
global.setImmediate = global.setImmediate || ((fn, ...args) => global.setTimeout(fn, 0, ...args));
global.clearImmediate = global.clearImmediate || ((id) => global.clearTimeout(id));

// Mock expo-router
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    canGoBack: jest.fn(() => true),
  }),
  useLocalSearchParams: () => ({}),
  useSegments: () => [],
  Link: ({ children }) => children,
  Redirect: () => null,
  Stack: {
    Screen: () => null,
  },
  Tabs: {
    Screen: () => null,
  },
}));

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(() => Promise.resolve(null)),
  setItemAsync: jest.fn(() => Promise.resolve()),
  deleteItemAsync: jest.fn(() => Promise.resolve()),
}));

// Mock @react-native-async-storage/async-storage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock expo-location
jest.mock('expo-location', () => ({
  requestForegroundPermissionsAsync: jest.fn(() =>
    Promise.resolve({ status: 'granted' })
  ),
  getCurrentPositionAsync: jest.fn(() =>
    Promise.resolve({
      coords: {
        latitude: -1.2921,
        longitude: 36.8219,
        altitude: 1700,
        accuracy: 10,
      },
    })
  ),
  watchPositionAsync: jest.fn(),
  Accuracy: {
    Balanced: 3,
    High: 4,
    Highest: 5,
    Low: 2,
    Lowest: 1,
  },
}));

// Mock expo-camera
jest.mock('expo-camera', () => ({
  useCameraPermissions: jest.fn(() => [
    { granted: true },
    jest.fn(() => Promise.resolve({ granted: true })),
  ]),
  CameraView: 'CameraView',
  CameraType: { back: 'back', front: 'front' },
}));

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  launchCameraAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: 'file://test-image.jpg' }],
    })
  ),
  launchImageLibraryAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: 'file://test-image.jpg' }],
    })
  ),
  requestCameraPermissionsAsync: jest.fn(() =>
    Promise.resolve({ status: 'granted' })
  ),
  MediaTypeOptions: { Images: 'Images' },
}));

// Mock expo-document-picker
jest.mock('expo-document-picker', () => ({
  getDocumentAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: 'file://test-doc.pdf', name: 'test.pdf', size: 1024 }],
    })
  ),
}));

// Mock react-native-maps
jest.mock('react-native-maps', () => {
  const { View } = require('react-native');
  return {
    __esModule: true,
    default: View,
    Marker: View,
    Polygon: View,
    Polyline: View,
    PROVIDER_GOOGLE: 'google',
  };
});

// Mock @expo/vector-icons
jest.mock('@expo/vector-icons', () => {
  const React = require('react');
  const { Text } = require('react-native');
  const Icon = (props) => React.createElement(Text, null, props.name || 'icon');
  return {
    Ionicons: Icon,
    MaterialIcons: Icon,
    FontAwesome: Icon,
    FontAwesome5: Icon,
    Feather: Icon,
    AntDesign: Icon,
    Entypo: Icon,
    createIconSet: () => Icon,
  };
});

// Mock expo-local-authentication
jest.mock('expo-local-authentication', () => ({
  hasHardwareAsync: jest.fn(() => Promise.resolve(true)),
  isEnrolledAsync: jest.fn(() => Promise.resolve(true)),
  authenticateAsync: jest.fn(() =>
    Promise.resolve({ success: true })
  ),
  AuthenticationType: { FINGERPRINT: 1, FACIAL_RECOGNITION: 2 },
}));

// Mock Animated for cleaner test output
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Silence console warnings in tests
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

beforeAll(() => {
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Animated') ||
        args[0].includes('useNativeDriver') ||
        args[0].includes('componentWillReceiveProps'))
    ) {
      return;
    }
    originalConsoleWarn.apply(console, args);
  };

  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('act(...)'))
    ) {
      return;
    }
    originalConsoleError.apply(console, args);
  };
});

afterAll(() => {
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;
});

// Global test utilities
global.mockApiResponse = (data, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {},
});

global.waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0));
