import queue
from ydl import ydl_send, ydl_start_read


events = queue.Queue()
ydl_start_read("PO", events)
while True:
    rcvd = events.get(block=True)
    print(f"RECEIVED: {rcvd}")
