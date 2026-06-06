const api = axios.create({ baseURL: '/api' });
async function loadProject(projectId) {
  const token = localStorage.getItem('token');
  return fetch(`/api/projects/${projectId}?tenantId=${window.tenantId}`, { headers: { Authorization: `Bearer ${token}` }});
}
function saveUser(userId, body) {
  return axios.post('/api/admin/users/' + userId, body);
}
const ws = new WebSocket('ws://localhost/ws/admin');
const q = gql`mutation DeleteUser($userId: ID!) { deleteUser(userId: $userId) { ok } }`;
