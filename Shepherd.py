from Utils import *

def LCM_receive(header, dic={}):
    global GAME_STATE
    print("GAME STATE OUTSIDE: ", GAME_STATE)
    print(header, dic)

    if GAME_STATE == STATE.SETUP:
        func = SETUP_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in Setup")
    elif GAME_STATE == STATE.END:
        func = END_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in End")
    elif GAME_STATE == STATE.CHANCELLOR:
        func = CHANCELLOR_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in Chancellor")
    elif GAME_STATE == STATE.VOTE:
        func = VOTE_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in Vote")
    elif GAME_STATE == STATE.POLICY:
        func = POLICY_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in Policy")
    elif GAME_STATE == STATE.ACTION:
        func = ACTION_FUNCTIONS.get(header)
        if func is not None:
            func(dic)
        else:
            print("Invalid Event in Action")
    else:
        print("Invalid State")


GAME_STATE = STATE.SETUP

SETUP_FUNCTIONS = {}
END_FUNCTIONS = {}
CHANCELLOR_FUNCTIONS = {}
VOTE_FUNCTIONS = {}
POLICY_FUNCTIONS = {}
ACTION_FUNCTIONS = {}
