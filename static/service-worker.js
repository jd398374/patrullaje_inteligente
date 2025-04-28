self.addEventListener('install', event => {
    console.log('[Service Worker] Instalando...');
    event.waitUntil(
      caches.open('patrullaje-cache-v1').then(cache => {
        return cache.addAll([
          '/',
          '/static/style.css',
          '/static/manifest.json',
          // Agrega aquí más rutas si quieres precachear otros archivos
        ]);
      })
    );
  });
  
  self.addEventListener('fetch', event => {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request);
        })
    );
  });
  