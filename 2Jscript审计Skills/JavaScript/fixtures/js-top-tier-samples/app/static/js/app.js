const apiBase = "/api/v2";
const token = localStorage.getItem("accessToken");
fetch(apiBase + "/tenant/" + localStorage.getItem("tenantId") + "/invoices", {headers:{Authorization:"Bearer "+token,"X-Tenant": localStorage.getItem("tenantId")}});
import("./lazy-admin.js");
const ws = new WebSocket("wss://example.invalid/ws/admin");
const q = gql`mutation Refund($id: ID!){ refundPayment(id:$id){ id status } }`;
window.addEventListener("message", e => { document.body.innerHTML = e.data.html; });
new Worker("/static/js/worker.js");
WebAssembly.instantiateStreaming(fetch("/assets/parser.wasm"));
//# sourceMappingURL=app.js.map
