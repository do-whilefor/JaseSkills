const api = axios.create({ baseURL: "/api" });
api.interceptors.request.use(x => x);
export async function loadUser(id) { return fetch(`/api/users/${id}?tenantId=tenant_a`); }
const hidden = { isAdmin: false, role: "admin", workspaceId: "w1" };
const q = `query UserHidden { user { id email tenantId } }`;
socket.emit("admin:update", { userId: 1 });
import("./lazy-admin.js");
localStorage.setItem("token", "abc");
//# sourceMappingURL=app.js.map
