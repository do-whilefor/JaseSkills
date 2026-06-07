import { apiGet, apiPost } from './apiClient.js';
import { loadAudit } from './nested/audit.js';
export async function loadUsers() { return apiGet('/admin/users?include=roles&tenantId=t1'); }
export async function saveUser(body) { return apiPost('/admin/users', body); }
export async function directFetch() { return fetch('/api/internal/feature-flags?debug=true'); }
export async function viaNested() { return loadAudit('/api/audit/events'); }
//# sourceMappingURL=userService.js.map
