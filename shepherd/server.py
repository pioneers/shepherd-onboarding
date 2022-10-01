import queue
import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from utils import *
from ydl import YDLClient
import gevent

HOST_URL = "0.0.0.0"
PORT = 5000

app = Flask(__name__)
app.config['SECRET_KEY'] = 'omegalul!'
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")

YC = YDLClient(YDL_TARGETS.UI)


@app.route('/')
def hello_world():
    return 'Hello, World!'

def password(_p):
    """
    checks to make sure p is the correct password
    password protection not used in this project
    """
    return True

@app.route('/<path:subpath>')
def give_page(subpath):
    """
    routing for all ui pages. Gives "page not found" if
    the page isn't in UI_PAGES, or prompts for password
    if the page is password protected
    """
    if subpath[-1] == "/":
        subpath = subpath[:-1]
    if subpath in UI_PAGES:
        passed = (not UI_PAGES[subpath]) or password(request.cookies.get('password'))
        return render_template(subpath if passed else "password.html")
    return "oops page not found"

@socketio.event
def connect():
    print('Established socketio connection')

@socketio.on('join')
def handle_join(name, id):
    join_room(id)
    print(f'confirmed join: {(name, id)}')

@socketio.on('ui-to-server')
def ui_to_server(p, header, args=None):
    if not password(p):
        return
    if args is None:
        YC.send((YDL_TARGETS.SHEPHERD, header, {}))
    else:
        YC.send((YDL_TARGETS.SHEPHERD, header, json.loads(args)))




def emit_to_rooms(message, data, recipients):
    for recipient in recipients:
        socketio.emit(message, json.dumps(data), room=recipient)

def emit_to_all(message, data):
    socketio.emit(message, json.dumps(data))


def receiver():
    while True:
        tpool = gevent.get_hub().threadpool
        event = tpool.spawn(YC.receive).get()
        print("RECEIVED:", event)
        header = event[1]
        data = event[2]

        if data.get('recipients', None) is not None:
            emit_to_rooms(header, data, data['recipients'])
        else:
            emit_to_all(header, data)
            
        socketio.sleep(0.1) # needed because neither windows not socketio play nice. A timeout on the events.get is not sufficient here.

if __name__ == "__main__":
    print("Hello, world!")
    print(f"Running server on port {PORT}. Pages:")
    for page in UI_PAGES:
        print(f"\thttp://localhost:{PORT}/{page}")

socketio.start_background_task(receiver)
socketio.run(app, host=HOST_URL, port=PORT)
