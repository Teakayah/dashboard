const CACHE_VERSION = 3;
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
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(ASSETS);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  event.respondWith((async () => {
    const response = await caches.match(event.request);
    return response || fetch(event.request);
  })());
});
