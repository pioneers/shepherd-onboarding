import queue
import threading
import time
from ydl import ydl_start_read, ydl_send
from utils import *


def listen_for_input():
    while True:
        val = input("Enter a message: ")
        if val == "repeat":
            wrapped_header = PONG_HEADERS.REPEAT()
            print(wrapped_header)
            ydl_send(*wrapped_header)
        else:
            wrapped_header = PONG_HEADERS.NOTIFY(text=val)
            print(wrapped_header)
            ydl_send(*wrapped_header)
        time.sleep(0.5); # wait for a response from pong
        

events = queue.Queue()
ydl_start_read(YDL_TARGETS.PING, events)
threading.Thread(target=listen_for_input, daemon=True).start()
while True:
    header, message = events.get(block=True)
    print(f"RECEIVED: {message['text']}")


