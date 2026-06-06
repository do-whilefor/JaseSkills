from flask import Flask, request, send_file
app = Flask(__name__)
DEBUG = True
JWT_SECRET = "redacted-fixture-secret"

@app.get('/api/users/<user_id>')
def user(user_id):
    tenant_id = request.args.get('tenantId')
    return {"user_id": user_id, "tenant_id": tenant_id}

@app.route('/admin/export')
def admin_export():
    return send_file(request.args.get('path', 'safe.txt'))

@app.post('/webhook/payment')
def payment_webhook():
    return 'ok'
