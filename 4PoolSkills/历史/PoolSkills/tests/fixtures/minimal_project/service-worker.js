self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/v1/export')) event.respondWith(fetch(event.request));
});
