from fastapi import FastAPI, Query, Depends
app = FastAPI()
def require_admin(): pass
@app.get('/api/audit/events')
async def audit_events(tenantId: str = Query(...), include: str = Query('')): return []
