from fastapi import FastAPI
app=FastAPI()
@app.get("/api/fastapi/admin")
def admin(): pass
# Django style tenant owner permission policy
