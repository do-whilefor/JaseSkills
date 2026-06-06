const API_BASE = '/api';
export async function loadUser(userId, include) {
  return fetch(`${API_BASE}/users/${userId}?include=${include}&preview=true`, { credentials: 'include' });
}
export async function loadAdmin() {
  const mod = await import('./admin-panel.js');
  return mod.open('/admin/debug/reindex');
}
const socket = new WebSocket('wss://example.invalid/ws/admin');
socket.emit('admin.audit.refresh', { tenantId: 't1' });
const query = `query HiddenUser($userId: ID!) { user(id: $userId) { id email } }`;
const isAdminPreviewEnabled = true;
