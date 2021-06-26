import queue
from ydl import ydl_send, ydl_start_read


events = queue.Queue()
ydl_start_read("PO", events)
n = 0
while n < 5:
    rcvd = events.get(block=True)
    print(f"RECEIVED: {rcvd}")
    n += 1
