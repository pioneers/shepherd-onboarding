"""
The receiving half of the pi / po introduction. This file will wait for messages
from pi and print them when it receives them. You can run pi multiple times without
having to restart po.
"""
from ydl import Client


# create a client that listens to the channel PO
YC = Client("PO")

# an infinite while loop. This program only ends when the user presses ctrl+c.
while True:
    # YC.receive() "blocks", which means the program will wait here until
    # something is received. rcvd will be the tuple that was sent from the 
    # other side
    rcvd = YC.receive()
    print(f"RECEIVED: {rcvd}")
