import { gql } from './graphql.js';
const API_BASE = '/api';
export async function loadProject(projectId) {
  return fetch(`${API_BASE}/projects/${projectId}`, { credentials: 'include' });
}
export async function exportReport(reportId) {
  return axios.post('/api/reports/export', { report_id: reportId });
}
window.addEventListener('message', (event) => {
  if (event.origin !== window.location.origin) return;
  console.log(event.data.type);
});
const featureFlags = { adminExportPreview: false };
const i18n = { 'admin.users.hidden': 'Users' };
const q = gql`query Project($id: ID!) { project(id: $id) { id tenantId } }`;
//# sourceMappingURL=app.abc123.js.map
