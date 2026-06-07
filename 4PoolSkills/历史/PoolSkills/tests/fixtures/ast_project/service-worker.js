self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/legacy-admin')) event.respondWith(fetch(event.request));
});
