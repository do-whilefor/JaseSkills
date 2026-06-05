navigator.serviceWorker.register('/sw.js');
const API_BASE = '/api';
fetch('/api/users/123');
fetch('/admin/export?format=json');
const gql = `query GetUser { user(id: "123") { id name } }`;
fetch('/graphql', {method:'POST', body: JSON.stringify({query: gql})});
const ws = new WebSocket('wss://local.test/ws/updates');
localStorage.setItem('debug_token','fixture-only-token');
window.postMessage({type:'fixture'}, '*');
const stripe_public_key = 'pk_test_1234567890abcdef';
//# sourceMappingURL=app.js.map
