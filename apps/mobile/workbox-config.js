module.exports = {
  globDirectory: 'dist/',
  globPatterns: ['**/*.{html,js,css,json,png,jpg,svg,woff,woff2,ttf}'],
  swDest: 'dist/sw.js',
  maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5 MB — precache the main bundle
  skipWaiting: true,
  clientsClaim: true,
  runtimeCaching: [
    {
      // JS, CSS, HTML — network-first so deploys are visible immediately
      urlPattern: /\.(?:js|css|html)$/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'static-resources',
        networkTimeoutSeconds: 3,
        expiration: {
          maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        },
      },
    },
    {
      // API calls — network-first with 5s timeout
      urlPattern: /\/api\/v1\//,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        networkTimeoutSeconds: 5,
        expiration: {
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
      },
    },
    {
      // Images — cache-first
      urlPattern: /\.(?:png|jpg|jpeg|gif|svg|webp|ico)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        },
      },
    },
    {
      // Fonts — cache-first
      urlPattern: /\.(?:woff|woff2|ttf|otf|eot)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'fonts',
        expiration: {
          maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
        },
      },
    },
  ],
};
