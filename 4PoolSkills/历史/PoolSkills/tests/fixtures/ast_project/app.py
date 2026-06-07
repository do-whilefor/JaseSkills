from flask import Flask, request
import os, subprocess, requests
app = Flask(__name__)

def login_required(fn):
    return fn

@app.route('/api/files/<path:name>', methods=['GET'])
@login_required
def read_file(name):
    tenant_id = request.args.get('tenantId')
    dry_run = request.args.get('dryRun')
    if dry_run == '1':
        return {'tenantId': tenant_id, 'preview': name}
    return open('/tmp/' + name).read()

@app.route('/api/hooks/preview', methods=['POST'])
def webhook_preview():
    callback = request.json.get('callbackUrl')
    return requests.get(callback).text
