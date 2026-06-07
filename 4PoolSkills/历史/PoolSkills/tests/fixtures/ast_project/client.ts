const API_BASE = '/api';
const tenantId = localStorage.getItem('tenantId');
const featureFlag = sessionStorage.getItem('previewMode');

export async function loadFile(fileId: string, hiddenAdminParam?: string) {
  return fetch(`${API_BASE}/files/${fileId}?tenantId=${tenantId}&preview=${featureFlag}`, {
    method: 'GET',
    headers: { 'X-Tenant-Id': tenantId || '', 'X-Debug-Trace': '0' }
  });
}

export async function previewWebhook(callbackUrl: string) {
  return apiClient.post('/api/hooks/preview', { callbackUrl, dryRun: true, admin: false, hiddenAdminParam });
}

const ws = new WebSocket(`wss://example.invalid/ws?tenantId=${tenantId}`);
navigator.serviceWorker.register('/service-worker.js');
window.postMessage({ type: 'tenant-switch', tenantId }, '*');
const q = `query HiddenProject($projectId: ID!) { project(id: $projectId) { id tenantId ownerId } }`;
import('./lazy-admin-panel');
