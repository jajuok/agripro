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

        // Detect new service worker waiting
        registration.addEventListener('updatefound', function () {
          var newWorker = registration.installing;
          if (!newWorker) return;

          newWorker.addEventListener('statechange', function () {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              // New version available — prompt user
              if (
                confirm(
                  'A new version of AgriPro is available. Reload to update?'
                )
              ) {
                newWorker.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
              }
            }
          });
        });
      })
      .catch(function (err) {
        console.warn('SW registration failed:', err);
      });
  });
}
