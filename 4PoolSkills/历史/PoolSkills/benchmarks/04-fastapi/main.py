from fastapi import FastAPI, Depends
app=FastAPI()
def require_user(): return {'id':1,'tenant':'a'}
@app.get('/items/{item_id}')
def read_item(item_id: int, user=Depends(require_user)):
    return {'item_id': item_id}
