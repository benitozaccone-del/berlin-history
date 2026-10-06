// Offline cache: app shell up front, photos/audio/map tiles cached as they are used.
// "Download all for offline" = open the app once on Wi-Fi; the shell precaches every place's photo and audio.
const CACHE = 'berlin-v7';

self.addEventListener('install', e => e.waitUntil((async () => {
  const c = await caches.open(CACHE);
  // cache:'reload' skips the browser's HTTP cache so a new version never precaches stale files
  await c.addAll(['./', 'index.html', 'manifest.json', 'icon.svg', 'apple-touch-icon.png', 'favicon-32.png', 'icon-192.png', 'icon-512.png', 'data/places.json', 'data/credits.json', 'data/story.json']
    .map(u => new Request(u, { cache: 'reload' })));
  const { places } = await (await fetch('data/places.json')).json();
  // best effort: missing MP3s (not yet generated) are simply skipped
  await Promise.allSettled([...places.flatMap(p => [c.add(`img/${p.id}.jpg`), c.add(`audio/${p.id}.mp3`)]), ...[1,2,3,4,5].map(i => c.add(`audio/chapter-${i}.mp3`))]);
  self.skipWaiting();
})()));

self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
  self.clients.claim();
})()));

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || e.request.headers.has('range')) return;
  const url = new URL(e.request.url);
  // page and data: network first so updates show up immediately; photos/audio/tiles: cache first
  if (e.request.mode === 'navigate' || url.pathname.endsWith('.json')) {
    e.respondWith(fetch(e.request, { cache: 'no-cache' }).then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
      .catch(() => caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
    if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
    return r;
  })));
});
