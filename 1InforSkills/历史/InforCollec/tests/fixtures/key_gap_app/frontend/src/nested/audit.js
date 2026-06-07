export function loadAudit(path) { return fetch(path, { method: 'GET', credentials: 'include' }); }
