from flask import request
import os, subprocess

def download():
    file_name = request.args.get('file')
    return open('/tmp/' + file_name).read()

def run():
    cmd = request.form.get('cmd')
    return subprocess.check_output(cmd, shell=True)
