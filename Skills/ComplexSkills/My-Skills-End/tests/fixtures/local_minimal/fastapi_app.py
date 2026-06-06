from fastapi import FastAPI
app = FastAPI()
@app.get('/api/projects/{id}')
def get_project(id: str):
    return {'id': id}
@app.post('/webhook/stripe')
def webhook():
    return {'ok': True}
