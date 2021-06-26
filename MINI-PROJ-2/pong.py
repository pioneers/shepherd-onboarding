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
    if BANNED:
        return
    if text in RESPONSES.CANNED_RESPONSES:
        response = RESPONSES.CANNED_RESPONSES[text]
        LAST_MESSAGE = response
        ydl_send(*PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time()))
    elif text in RESPONSES.BANNED_RESPONSES:
        BANNED = True


def respond_to_repeat():
    if LAST_MESSAGE is not None and not BANNED:
        ydl_send(*PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time()))

HEADER_MAPPINGS = {
    PONG_HEADERS.NOTIFY.name: respond_to_notify,
    PONG_HEADERS.REPEAT.name: respond_to_repeat
}

if __name__ == '__main__':
    start()







