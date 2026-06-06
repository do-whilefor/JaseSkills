from fastapi import FastAPI, Depends
app = FastAPI()

def require_user():
    return {"role": "user", "tenant": "tenant_a"}

@app.get("/api/projects/{project_id}")
def read_project(project_id: str, user=Depends(require_user)):
    return {"id": project_id, "tenant": user["tenant"]}

@app.post("/api/reports/export")
def export_report(report_id: str, user=Depends(require_user)):
    return {"status": "queued", "report_id": report_id}
