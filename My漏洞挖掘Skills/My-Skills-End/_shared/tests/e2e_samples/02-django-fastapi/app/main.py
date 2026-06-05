from fastapi import FastAPI
app=FastAPI()
@app.get('/api/projects/{id}')
def x(id): return raw_query('select * from p where id='+id)
@app.post('/webhook/stripe')
def w(): return verify_signature()
