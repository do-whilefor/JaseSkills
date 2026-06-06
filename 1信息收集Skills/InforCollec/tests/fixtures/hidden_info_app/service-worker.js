self.addEventListener('install', event => { caches.open('v1').then(c => c.addAll(['/offline.html','/api/offline/admin-cache'])); });
