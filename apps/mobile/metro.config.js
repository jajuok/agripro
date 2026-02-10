const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

// Find the project and workspace directories
const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

// 1. Watch all files within the monorepo
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

// 3. Force resolving these modules correctly
// 'expo' must resolve to the mobile workspace version (SDK 50) to match the native build,
// not the root monorepo version (SDK 54) which requires native modules not present in SDK 50.
config.resolver.extraNodeModules = {
  ...config.resolver.extraNodeModules,
  'expo': path.resolve(projectRoot, 'node_modules/expo'),
  'expo-asset': path.resolve(monorepoRoot, 'node_modules/expo-asset'),
  'expo-router': path.resolve(monorepoRoot, 'node_modules/expo-router'),
  'react': path.resolve(monorepoRoot, 'node_modules/react'),
  'react-native': path.resolve(monorepoRoot, 'node_modules/react-native'),
};

// 4. Ensure we're looking in the right places for assets
config.resolver.assetExts = config.resolver.assetExts || [];

module.exports = config;
