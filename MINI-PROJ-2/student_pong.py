import queue
import time
from ydl import ydl_start_read, ydl_send
from utils import *

BANNED = False
LAST_MESSAGE = None


def start():
    events = queue.Queue()
    ydl_start_read(YDL_TARGETS.PONG, events)
    while True:
        header, message = events.get(block=True)
        print(f"received: {(header, message)}")
        if header in HEADER_MAPPINGS:
            HEADER_MAPPINGS.get(header)(**message)


def respond_to_notify(text):
    global BANNED, LAST_MESSAGE
    if text in RESPONSES.CANNED_RESPONSES:
        response = RESPONSES.CANNED_RESPONSES[text]
        ydl_send(*PING_HEADERS.RESPOND(text=response, time=time.time()))
        LAST_MESSAGE = response

    ###### YOUR CODE HERE ######


def respond_to_repeat():

    ###### YOUR CODE HERE ######
    pass

HEADER_MAPPINGS = {
    PONG_HEADERS.NOTIFY.name: respond_to_notify,
    PONG_HEADERS.REPEAT.name: respond_to_repeat
}

if __name__ == '__main__':
    start()
