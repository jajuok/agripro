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

// 3. Force resolving these modules from the monorepo root
config.resolver.extraNodeModules = {
  ...config.resolver.extraNodeModules,
  'expo-router': path.resolve(monorepoRoot, 'node_modules/expo-router'),
  'expo': path.resolve(monorepoRoot, 'node_modules/expo'),
  'react': path.resolve(monorepoRoot, 'node_modules/react'),
  'react-native': path.resolve(monorepoRoot, 'node_modules/react-native'),
};

// 4. Ensure we're looking in the right places for assets
config.resolver.assetExts = config.resolver.assetExts || [];

module.exports = config;
