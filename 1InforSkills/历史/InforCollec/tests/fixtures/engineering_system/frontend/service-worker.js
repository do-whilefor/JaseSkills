self.__WB_MANIFEST = [{url: '/admin/offline.html'}, {url: '/api/internal/cache-only'}];
workbox.routing.registerRoute('/api/reports/export', new workbox.strategies.NetworkFirst());
