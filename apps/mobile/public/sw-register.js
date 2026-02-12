if ('serviceWorker' in navigator && location.protocol === 'https:') {
  window.addEventListener('load', function () {
    navigator.serviceWorker
      .register('/sw.js')
      .then(function (registration) {
        console.log('SW registered:', registration.scope);

        // Check for updates periodically
        setInterval(function () {
          registration.update();
        }, 5 * 60 * 1000); // every 5 minutes
      })
      .catch(function (err) {
        console.warn('SW registration failed:', err);
      });

    // Auto-reload when a new service worker takes control.
    // This fires after skipWaiting + clientsClaim activate a new SW,
    // guaranteeing the page reloads with fresh content after every deploy.
    var refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (refreshing) return;
      refreshing = true;
      console.log('New SW activated — reloading for update');
      window.location.reload();
    });
  });
}
