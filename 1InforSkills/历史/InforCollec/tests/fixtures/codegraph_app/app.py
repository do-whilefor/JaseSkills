from flask import Flask, request
app = Flask(__name__)

@app.route('/api/projects/<project_id>')
def project(project_id):
    require_user()
    return db.query('select * from projects where id=' + project_id)
