export async function apiGet(path: string) { return fetch('/api' + path, { headers: { 'x-tenant-id': 'tenant_a' }}); }
export const loadAdmin = () => import('./chunks/admin-panel');
apiGet('/projects/123?owner_id=7');
//# sourceMappingURL=client.js.map
localStorage.setItem('tenant','tenant_a');
window.postMessage({type:'safe_probe'}, '*');
const api_key = "1234567890abcdef";
