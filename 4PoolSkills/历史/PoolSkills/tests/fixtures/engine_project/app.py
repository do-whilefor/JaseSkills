from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/api/users/{user_id}")
def get_user(user_id: str, tenantId: str = None):
    query = "select * from users where id = " + user_id
    return {"query": query, "tenantId": tenantId}

@app.post("/api/admin/update")
def update_admin(request: Request):
    body = request.__dict__  # role/isAdmin mass assignment signal
    return body
