const CACHE_NAME = 'datadashboard-v1';
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
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
