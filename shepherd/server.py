import queue
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from utils import *
from ydl import ydl_send, ydl_start_read

HOST_URL = "0.0.0.0"
PORT = 5000
last_header = None

app = Flask(__name__)
socketio = SocketIO(app, async_mode="gevent")


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/test')
def testy_boi():
    return render_template('testing.html')


@app.route('/game')
def game():
    return render_template('game.html')


@socketio.on('join')
def on_join(user_info):
    data = json.loads(user_info)
    username = data['name']
    id = data['id']
    join_room(id)
    print('confirmed join: ', id)
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PLAYER_JOINED,
             {"name": username, "id": id})




@socketio.on('next_stage')
def next_stage():
    print('request to transition to next stage')
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.NEXT_STAGE)


@socketio.on('chancellor_nomination')
def chancellor_nomination(chancellor_info):
    data = json.loads(chancellor_info)
    print('chancellor has been nominated to be ', data['nominee'])
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_NOMINATION, data)


@socketio.on('player_voted')
def player_voted(vote_info):
    # BEGIN QUESTION 1
    data = json.loads(vote_info)
    print('Player with id: ', data['id'], ' has voted ', data['vote'])
    ydl_send(_____________, _________________, _______________)
    # END QUESTION 1


@socketio.on('president_discarded')
def president_discarded(policy_info):
    # BEGIN QUESTION 2
    data = json.loads(policy_info)
    print(data)
    print('after president discarded',
          data['discarded'], ', cards remaining are: ', data['cards'])
    ydl_send(_______________, _________________, _______________)
    # END QUESTION 2


@socketio.on('chancellor_discarded')
def chancellor_discarded(policy_info):
    data = json.loads(policy_info)
    print('after chancellor discarded',
          data['discarded'], ', card remaining is: ', data['card'])
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_DISCARDED, data)


@socketio.on('chancellor_vetoed')
def chancellor_vetoed(veto_info):
    print('chancellor vetoed :(')
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_VETOED)


@socketio.on('president_veto_answer')
def president_veto_answer(veto_info):
    data = json.loads(veto_info)
    print('did president decide to veto? ',
          data['veto'], '. Cards for chancellor are: ', data['cards'])
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER, data)


@socketio.on('end_policy_peek')
def end_policy_peek(peek_info):
    print('policy peek over.')
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.END_POLICY_PEEK)


@socketio.on('investigate_player')
def investigate_player(player_info):
    data = json.loads(player_info)
    print('Decided to investigate ', data['player'])
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.INVESTIGATE_PLAYER, data)


@socketio.on('end_investigate_player')
def end_investigate_player(player_info):
    print('investigation over.')
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.END_INVESTIGATE_PLAYER)


@socketio.on('special_election_pick')
def special_election_pick(player_info):
    data = json.loads(player_info)
    print('President picked ', data['player'], ' through special election.')
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK, data)


@socketio.on('perform_execution')
def perform_execution(player_info):
    data = json.loads(player_info)
    print('Perform execution on ', data['player'])
    ydl_send(YDL_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PERFORM_EXECUTION, data)


def emit_to_rooms(message, data, recipients):
    for recipient in recipients:
        socketio.emit(message, json.dumps(data), room=recipient)


def emit_to_all(message, data):
    socketio.emit(message, json.dumps(data))


def receiver():
    global last_header

    events = queue.Queue()
    ydl_start_read(YDL_TARGETS.UI, events)
    while True:
        while not events.empty():
            header, data = events.get() # ("cheese", {"a":1})
            print("RECEIVED:", header, data)
            
            if header == SERVER_HEADERS.REPEAT_MESSAGE and last_header:
                recipients = data['recipients']
                header, data = last_header
                data['recipients'] = recipients
                print("sending last privileged header:\n", header, data)
            # TODO: delete above 5 lines

            if data.get('recipients', []):
                emit_to_rooms(header, data, data['recipients'])
            else:
                emit_to_all(header, data)
            if header in LCM_UTILS.PRIVILEGED_HEADERS:
                last_header = (header, data)
        socketio.sleep(0.1)

if __name__ == "__main__":
    print("Hello, world!")
    print(f"Running server on port {PORT}. Pages:")
    for page in UI_PAGES:
        print(f"\thttp://localhost:{PORT}/{page}")

socketio.start_background_task(receiver)
socketio.run(app, host=HOST_URL, port=PORT)
