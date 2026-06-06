from fastapi import FastAPI
app=FastAPI()
@app.get('/api/projects/{id}')
def project(id:int): return {'id':id}
