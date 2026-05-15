const CACHE_VERSION = 2;
const CACHE_NAME = `datadashboard-v${CACHE_VERSION}`;
const ASSETS = [
  '/',
  '/index.html',
  '/assets/theme.css',
  '/assets/fullscreen.js',
  '/dropzone/vendor/gridjs/gridjs.js',
  '/dropzone/vendor/gridjs/mermaid.min.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
