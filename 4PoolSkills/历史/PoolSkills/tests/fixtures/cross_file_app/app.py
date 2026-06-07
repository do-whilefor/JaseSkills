from flask import Flask, request
from service import dangerous_lookup
app = Flask(__name__)

@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    tenantId = request.args.get('tenantId')
    return dangerous_lookup(item_id, tenantId)
