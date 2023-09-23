"""
The receiving half of the ping / pong mini project. This file will take inputs from
ping and process them. It will then send the processed message along with a time
stamp back to ping. If ping sends a banned message, pong will refuse to send anything
back ever again.
"""
import time
from ydl import Client, Handler
from utils import *

# global variable to keep track of if we have decided to stop sending messages
# to ping.
BANNED = False
# global variable to keep track of the last message so that we can repeat it.
LAST_MESSAGE = None
# create a client that listens to the channel YDL_TARGETS.PONG
YC = Client(YDL_TARGETS.PONG)
PONG_HANDLER = Handler()


def start():
    """
    The main function for pong is this start function. This function contains the
    ydl loop that reads messages from ping and correctly dispatches them to an
    appropriate function.
    """
    # an infinite while loop. This program only ends when the user presses ctrl+c.
    while True:
        # YC.receive() "blocks", which means the program will wait here until
        # something is received.
        data = YC.receive()
        # print out the received message for transparency.
        print(f"received: {data}")
        # if we get a header that we know how to process, dispatch it to the
        # correct function.
            # get the correct function from our mappings and call this function
            # will the message from the header as arguments.
            # ** turns a dictionary into keyword arguments, allowing us to call
            # the function easily. This is the same as writing:
            # HEADER_MAPPINGS.get(header)(arg = message[arg]) for every arg in
            # the function. We do it this way, because each function has different
            # args, so writing it all out would be next to impossible.
        PONG_HANDLER.handle(YC.receive)

# this is a decorator, which is a feature of python that allows us to modify functions
# here, we are modifying the function respond_to_notify so that it is called whenever
# we receive a message with the header PING_HEADERS.NOTIFY
@PONG_HANDLER.on(PING_HEADERS.NOTIFY)
def respond_to_notify(text):
    """
    The function called to respond to a notify header. This function makes sure
    that the message that was received was not a banned message and also substitutes
    any canned responses. If there is a banned message, BANNED will be set to true,
    and if BANNED is set to true, no more messages will be sent back to ping.
    Lastly, this function sends the message back to ping along with a time stamp.
    """
    # import variables from the global scope.
    global BANNED, LAST_MESSAGE
    # if banned, we want to do nothing
    if BANNED:
        return
    # if we get something we have a canned response for, send the canned response
    if text in RESPONSES.CANNED_RESPONSES:
        # get the answer from the utils file.
        response = RESPONSES.CANNED_RESPONSES[text]
        # save our answer as our last message so repeat can use it.
        LAST_MESSAGE = response
        # construct a tuple from the header with the appropriate args and
        # send the header via ydl_send. The tuple returned from PING_HEADERS.RESPOND
        # contains (ydl_target, header_name, data).
        YC.send(PING_HEADERS.RESPOND(response, time.time()))
    # if we get a banned message, ban the user.
    elif text in RESPONSES.BANNED_RESPONSES:
        BANNED = True
    # otherwise, just echo the message
    else:
        # see above comments; only difference is we're saving and sending
        # the original message instead of a canned response
        LAST_MESSAGE = text
        YC.send(PING_HEADERS.RESPOND(text, time.time()))
    
# this function will be called whenever we receive a message with the header
# PING_HEADERS.REPEAT
@PONG_HANDLER.on(PING_HEADERS.REPEAT)
def respond_to_repeat():
    """
    Send the most recent response back to ping via ydl so long as we are not banned.
    """
    # make sure there is a last message, and that the user is not banned.
    if LAST_MESSAGE is not None and not BANNED:
        # construct a tuple from the header with the appropriate args and
        # send the header via ydl_send. The tuple returned from PING_HEADERS.RESPOND
        # contains (ydl_target, header_name, data).
        YC.send(PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time()))


# run start() when this program is run.
if __name__ == '__main__':
    start()
