"""
The receiving half of the pi / po introduction. This file will wait for messages
from pi and print them when it receives them. You can run pi multiple times without
having to restart po.
"""
from ydl import YDLClient


# create a client that listens to the channel PO
YC = YDLClient("PO")

# instead of "while True", which loops forever, this will only listen
# for 5 messages
for _ in range(5):
    # YC.receive() "blocks", which means the program will wait here until
    # something is received. rcvd will be the tuple that was sent from the 
    # other side
    rcvd = YC.receive()
    print(f"RECEIVED: {rcvd}")
