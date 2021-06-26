"""
The receiving half of the ping / pong mini project. This file will take inputs from
ping and process them. It will then send the processed message along with a time
stamp back to ping. If ping sends a banned message, pong will refuse to send anything
back ever again.
"""
# all of our imports
import queue
import time
from ydl import ydl_start_read, ydl_send
from utils import *

# global variable to keep track of if we have decided to stop sending messages
# to ping.
BANNED = False
# global variable to keep track of the last message so that we can repeat it.
LAST_MESSAGE = None


def start():
    """
    The main function for pong is this start function. This function contains the
    ydl loop that reads messages from ping and correctly dispatches them to an
    appropriate function.
    """
    # create a new queue for ydl to store received messages in.
    # a queue is a FIFO data structure that you can pull data from one entry at a
    # time. Read more about this here:
    # https://en.wikipedia.org/wiki/Queue_(abstract_data_type)
    events = queue.Queue()
    # start ydl and tell it the target we want to read from. YDL will put any messages
    # into the queue that we provide.
    ydl_start_read(YDL_TARGETS.PONG, events)
    # an infinite while loop. This program only ends when the user presses ctrl+c.
    while True:
        # wait for a message to be put into our queue by ydl. Since we have set this
        # to blocking, python execution will not continue to the next line until
        # there is something in the queue for us to get.
        # reading from the queue removes the read data from the queue, leaving the
        # queue empty again.
        header, message = events.get(block=True)
        # print out the received message for transparency.
        print(f"received: {(header, message)}")
        # if we get a header that we know how to process, dispatch it to the
        # correct function.
        if header in HEADER_MAPPINGS:
            # get the correct function from our mappings and call this function
            # will the message from the header as arguments.
            # ** turns a dictionary into keyword arguments, allowing us to call
            # the function easily. This is the same as writing:
            # HEADER_MAPPINGS.get(header)(arg = message[arg]) for every arg in
            # the function. We do it this way, because each function has differnt
            # args, so writing it all out would by next to impossible.
            HEADER_MAPPINGS.get(header)(**message)

def respond_to_notify(text):
    """
    The function called to respond to a notify header. This function makes sure
    that the message that was received was not a banned message and also substitutes
    any canned responses. If there is a banned message, BANNED will be set to true,
    and if BANNED is set to true, no more messages will be sent back to ping.
    Lastly, this function sends the message back to ping along with a time stamp.
    """
    # import varaibles from the global scope.
    global BANNED, LAST_MESSAGE
    # if banned, we want to do nothing
    if BANNED:
        return
    # if we get a canned response, lets swap it with our answer.
    if text in RESPONSES.CANNED_RESPONSES:
        # get the anwer from the utils file.
        response = RESPONSES.CANNED_RESPONSES[text]
        # save our answer as our last message so repeat can use it.
        LAST_MESSAGE = response
        # construct a tuple from the header with the appropriate args and
        # send the header via ydl_send. The tuple returned from PING_HEADERS.RESPOND
        # contains (ydl_target, header_name, data). The * operator breaks the tuple
        # into 3 arguments (since the tuple is length 3) and sets them in the
        # function call. This is just a short and simple way to write:
        # wrapped_header = PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time())
        # ydl_send(wrapped_header[0], wrapped_header[1], wrapped_header[2])
        ydl_send(*PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time()))
    # if we get a banned message, ban the user.
    elif text in RESPONSES.BANNED_RESPONSES:
        BANNED = True
    # otherwise, just echo the message
    else:
        # see above comments; only difference is we're saving and sending
        # the original message instead of a canned response
        LAST_MESSAGE = text
        ydl_send(*PING_HEADERS.RESPOND(text=text, time=time.time()))
    


def respond_to_repeat():
    """
    Send the most recent response back to ping via ydl so long as we are not banned.
    """
    # make sure there is a last message, and that the user is not banned.
    if LAST_MESSAGE is not None and not BANNED:
        # construct a tuple from the header with the appropriate args and
        # send the header via ydl_send. The tuple returned from PING_HEADERS.RESPOND
        # contains (ydl_target, header_name, data). The * operator breaks the tuple
        # into 3 arguments (since the tuple is length 3) and sets them in the
        # function call. This is just a short and simple way to write:
        # wrapped_header = PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time())
        # ydl_send(wrapped_header[0], wrapped_header[1], wrapped_header[2])
        ydl_send(*PING_HEADERS.RESPOND(text=LAST_MESSAGE, time=time.time()))

# a mapping of header names to the functions that will be called to handle that header.
HEADER_MAPPINGS = {
    PONG_HEADERS.NOTIFY.name: respond_to_notify,
    PONG_HEADERS.REPEAT.name: respond_to_repeat
}

# run start() when this program us run.
if __name__ == '__main__':
    start()
