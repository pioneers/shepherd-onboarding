import json
import threading
import time
import queue
import gevent  # pylint: disable=import-error
import flask_login
import Shepherd
from flask import Flask, render_template  # pylint: disable=import-error
from flask_socketio import SocketIO, emit, join_room, leave_room, send  # pylint: disable=import-error
from Utils import *
from LCM import lcm_send, lcm_register

HOST_URL = "127.0.0.1"
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

# @app.route('/game')
# def render_board():
#     return render_template('game.html')


@socketio.on('join')
def on_join(user_info):
    data = json.loads(user_info)
    username = data['name']
    id = data['id']
    join_room(id)
    print('confirmed join: ', id)
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PLAYER_JOINED,
             {"name": username, "id": id})


@app.route('/game')
def game():
    return render_template('game.html')


@socketio.on('next_stage')
def next_stage():
    print('request to transition to next stage')
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.NEXT_STAGE)


@socketio.on('chancellor_nomination')
def chancellor_nomination(chancellor_info):
    data = json.loads(chancellor_info)
    print('chancellor has been nominated to be ', data['nominee'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_NOMINATION, data)


@socketio.on('player_voted')
def player_voted(vote_info):
    """
    BEGIN QUESTION 1
    data = json.loads(vote_info)
    print('Player with id: ', data['id'], ' has voted ', data['vote'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PLAYER_VOTED, data)
    """


@socketio.on('president_discarded')
def president_discarded(policy_info):
    """
    BEGIN QUESTION 2
    data = json.loads(policy_info)
    print(data)
    print('after president discarded',
          data['discarded'], ', cards remaining are: ', data['cards'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PRESIDENT_DISCARDED, data)
    """


@socketio.on('chancellor_discarded')
def chancellor_discarded(policy_info):
    data = json.loads(policy_info)
    print('after chancellor discarded',
          data['discarded'], ', card remaining is: ', data['card'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_DISCARDED, data)


@socketio.on('chancellor_vetoed')
def chancellor_vetoed(veto_info):
    print('chancellor vetoed :(')
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.CHANCELLOR_VETOED)


@socketio.on('president_veto_answer')
def president_veto_answer(veto_info):
    data = json.loads(veto_info)
    print('did president decide to veto? ',
          data['veto'], '. Cards for chancellor are: ', data['cards'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER, data)


@socketio.on('end_policy_peek')
def end_policy_peek(peek_info):
    print('policy peek over.')
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.END_POLICY_PEEK)


@socketio.on('investigate_player')
def investigate_player(player_info):
    data = json.loads(player_info)
    print('Decided to investigate ', data['player'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.INVESTIGATE_PLAYER, data)


@socketio.on('end_investigate_player')
def end_investigate_player(player_info):
    print('investigation over.')
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.END_INVESTIGATE_PLAYER)


@socketio.on('special_election_pick')
def special_election_pick(player_info):
    data = json.loads(player_info)
    print('President picked ', data['player'], ' through special election.')
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK, data)


@socketio.on('perform_execution')
def perform_execution(player_info):
    data = json.loads(player_info)
    print('Perform execution on ', data['player'])
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADERS.PERFORM_EXECUTION, data)


def emit_to_rooms(message, data, recipients):
    for recipient in recipients:
        socketio.emit(message, json.dumps(data), room=recipient)


def emit_to_all(message, data):
    socketio.emit(message, json.dumps(data))


def LCM_receive(header, data={}):
    global last_header
    print("server.py: LCM_receive", header, data)
    if header == SERVER_HEADERS.REPEAT_MESSAGE and last_header:
        recipients = data['recipients']
        header = last_header[0]
        data = last_header[1]
        data['recipients'] = recipients
        print("sending last privileged header:")
        print(header, data)
    if data.get('recipients', []):
        emit_to_rooms(header, data, data['recipients'])
    else:
        emit_to_all(header, data)
    if header in LCM_UTILS.PRIVILEGED_HEADERS:
        last_header = (header, data)
#     events = gevent.queue.Queue()
#     lcm_start_read(str.encode(LCM_TARGETS.UI), events)

#     while True:

#         if not events.empty():
#             event = events.get_nowait()
#             print("RECEIVED:", event)
#             if event[0] == UI_HEADER.TEAMS_INFO:
#                 socketio.emit('server-to-ui-teamsinfo', json.dumps(event[1], ensure_ascii=False))
#             elif event[0] == UI_HEADER.SCORES:
#                 socketio.emit('server-to-ui-scores', json.dumps(event[1], ensure_ascii=False))
#             elif event[0] == UI_HEADER.CONNECTIONS:
#                 socketio.emit('server-to-ui-connections', json.dumps(event[1], ensure_ascii=False))
#         socketio.sleep(0.1)

# socketio.start_background_task(receiver)


lcm_register(LCM_TARGETS.SERVER, LCM_receive)
lcm_register(LCM_TARGETS.SHEPHERD, Shepherd.LCM_receive)

socketio.run(app, host=HOST_URL, port=PORT)
