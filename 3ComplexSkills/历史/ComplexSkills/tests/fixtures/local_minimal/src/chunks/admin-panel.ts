export function openAdminSocket() { const ws = new WebSocket('ws://localhost:3000/admin'); ws.send(JSON.stringify({type:'admin.read', tenant_id:'tenant_b'})); }
