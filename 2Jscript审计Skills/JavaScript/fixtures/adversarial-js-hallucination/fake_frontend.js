// adversarial fixture: all findings are candidate only
const secretKeyword = 'not-a-secret';
const disabled = true;
if(false){ fetch('/admin/fake/deleteEverything', { method:'POST', body: JSON.stringify({tenantId:'demo'}) }); }
window.addEventListener('message', e => { console.log(e.data); });
const q = `query Fake { user(id:"1") { impossibleField } }`;
