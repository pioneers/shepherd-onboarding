"""
The sending half of the ping / pong mini project. This file will take inputs from
the terminal and send them to pong. It will also print out messages received from
pong.
"""
import threading
import time
from ydl import Client
from utils import YDL_TARGETS, PONG_HEADERS


def listen_for_input():
    """
    A function which will run in its own thread to capture input from the terminal
    and send that input to pong.
    Don't worry too much about how this works, just know that it runs at the same
    time as the main ydl loop.
    contains a while loop that will wait for a message to be typed in the terminal
    via stdin. Once a message is detected it will check to see if the message was
    'repeat' and will send the appropriate ydl header to pong.
    """
    # an infinite while loop. This program only ends when the user presses ctrl+c.
    while True:
        # get a value from the terminal via stdin. This will print the given 
        # prompt and then wait for a response. input is blocking, so python 
        # execution will stop until the user inputs something.
        val = input("Enter a message: ")
        # check if the user wrote 'repeat'.
        if val == "repeat":
            # create a header to be passed into YC.send. This wrapped header is
            # a tuple returned by PONG_HEADERS.REPEAT(), which looks like:
            # (ydl_target, header_name, data).
            wrapped_header = PONG_HEADERS.REPEAT()
        # otherwise we want to pass along the message to pong.
        else:
            # create a header to be passed into YC.send. This wrapped header is
            # a tuple returned by PONG_HEADERS.REPEAT(), which looks like:
            # (ydl_target, header_name, data).
            wrapped_header = PONG_HEADERS.NOTIFY(text=val)
        # print out the wrapped header so you can see what is in it.
        print(f"sent: {wrapped_header}")
        # send the header via YC.send.
        YC.send(wrapped_header)
        # wait for a response from pong. This is necessary to make the terminal
        # look nice.
        time.sleep(0.5)

# create a client that listens to the channel YDL_TARGETS.PING
YC = Client(YDL_TARGETS.PING)
# spawn our thread that listens for terminal inputs.
threading.Thread(target=listen_for_input, daemon=True).start()
# an infinite while loop. This program only ends when the user presses ctrl+c.
while True:
    # YC.receive() "blocks", which means the program will wait here until
    # something is received.
    channel, header, message = YC.receive()
    # print out the received message
    print(f"received message: {message['text']}")
    # since message['time'] stores the time that the message was sent, the 
    # elapsed time is how long it took to send through YDL.
    print(f"time taken: {time.time() - message['time']} seconds")
