"""
The sending half of the ping / pong mini project. This file will take inputs from
the terminal and send them to pong. It will also print out messages received from
pong.
"""
import queue
import threading
import time
from ydl import ydl_start_read, ydl_send
from utils import *


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
    while True:
        # get a value from the terminal via stdin. This will print the given 
        # prompt and then wait for a response. input is blocking, so python 
        # execution will stop until the user inputs something.
        val = input("Enter a message: ")
        # check if the user wrote 'repeat'.
        if val == "repeat":
            # create a header to be passed into ydl_send. This wrapped header is
            # a tuple returned by PONG_HEADERS.REPEAT(), which looks like:
            # (ydl_target, header_name, data).
            wrapped_header = PONG_HEADERS.REPEAT()
        # otherwise we want to pass along the message to pong.
        else:
            # create a header to be passed into ydl_send. This wrapped header is
            # a tuple returned by PONG_HEADERS.REPEAT(), which looks like:
            # (ydl_target, header_name, data).
            wrapped_header = PONG_HEADERS.NOTIFY(text=val)
        # print out the wrapped header so you can see what is in it.
        print(wrapped_header)
        # send the header via ydl_send. The * operator breaks the tuple into
        # 3 arguments (since the tuple is length 3) and sets them in the
        # function call. This is just a short and simple way to write:
        # ydl_send(wrapped_header[0], wrapped_header[1], wrapped_header[2])
        ydl_send(*wrapped_header)
        # wait for a response from pong. This is necessary to make the terminal
        # look nice.
        time.sleep(0.5)
        
# create a new queue for ydl to store received messages in.
# a queue is a FIFO data structure that you can pull data from one entry at a
# time. Read more about this here:
# https://en.wikipedia.org/wiki/Queue_(abstract_data_type)
events = queue.Queue()
# start ydl and tell it the target we want to read from. YDL will put any messages
# into the queue that we provide.
ydl_start_read(YDL_TARGETS.PING, events)
# spawn our thread that listens for terminal inputs.
threading.Thread(target=listen_for_input, daemon=True).start()
# an infinite while loop. This program only ends when the user presses ctrl+c.
while True:
    # wait for a message to be put into our queue by ydl. Since we have set this
    # to blocking, python execution will not continue to the next line until
    # there is something in the queue for us to get.
    # reading from the queue removes the read data from the queue, leaving the
    # queue empty again.
    header, message = events.get(block=True)
    # print out the received message
    print(f"RECEIVED: {message['text']}")
    ###### YOUR CODE HERE ######


