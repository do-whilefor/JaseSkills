const api = axios.create({ baseURL: '/api' });
export async function updateUser(id, email) {
  return api.patch(`/users/${id}`, { email });
}
export const UserUpdate = { email: 'string', role: 'string', isAdmin: 'boolean', tenantId: 'string', quota: 'number' };
const gql = `mutation UpdateUser($id: ID!, $role: String, $tenantId: ID) { updateUser(id:$id, role:$role, tenantId:$tenantId) { id role tenantId } }`;
const ws = new WebSocket('/ws/admin');
ws.send(JSON.stringify({type:'user.promote', userId:'u1', role:'admin'}));
