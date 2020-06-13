import json
from flask import Flask, render_template, request # pylint: disable=import-error

HOST_URL = "127.0.0.1" 
PORT = 5500

app = Flask(__name__)

@app.route('/')
def hello():
    return 'hello world'
