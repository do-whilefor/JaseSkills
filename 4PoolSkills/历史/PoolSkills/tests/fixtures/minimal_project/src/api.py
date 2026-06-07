from fastapi import FastAPI, Depends
app = FastAPI()
def current_user(): return {'id': 1, 'role': 'user'}
@app.get('/api/v1/orders/{order_id}')
def order(order_id: str, user=Depends(current_user)): return {'id': order_id}
@app.post('/api/v1/graphql')
def graphql(): return {}
