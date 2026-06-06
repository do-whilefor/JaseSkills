import api from './client';
const routes=[{path:'/admin/refund/:orderId', component:'RefundPanel'}];
export async function refund(orderId, tenantId){
  if (!window.currentUser?.roles?.includes('admin')) return;
  return fetch('/api/admin/refund', {method:'POST', headers:{'X-Tenant':tenantId}, body:JSON.stringify({orderId, tenantId, amountOverride: 1})});
}
const ws = new WebSocket('/ws/admin');
ws.send(JSON.stringify({type:'tenant.switch', tenantId: localStorage.tenantId}));
window.addEventListener('message', event => { document.body.innerHTML = event.data.html; });
const query = `query User($id:ID!){ user(id:$id){ id email tenantId } }`;
