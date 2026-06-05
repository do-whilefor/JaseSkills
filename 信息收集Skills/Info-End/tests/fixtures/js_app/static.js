// webpack fixture
var __webpack_require__ = {};
const api = axios.get('/api/admin/export?userId=123');
const ws = new WebSocket('/ws/tenant/tenant-1');
const q = gql`mutation UpdateRole($userId: ID!, $roleId: ID!) { updateRole(userId:$userId, roleId:$roleId) { id } }`;
const p = new URLSearchParams(location.search).get('redirect');
window.addEventListener('message', event => { document.body.innerHTML = event.data.html; });
//# sourceMappingURL=static.js.map
