from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix="/v2")
@app.get("/healthz")
def health(): pass
@router.post("/tenant/{tenant_id}/invoice")
def invoice(tenant_id: str): pass
