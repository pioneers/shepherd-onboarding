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

#===================================
# game functions
#===================================

def player_joined(args):
    global PLAYERS
    id = args["id"]
    name = args["name"]
    #send data to player with that id
    if not id in PLAYERS:
        PLAYERS += [Player(id, name)]
        #send data about that player joining to everyone


#===================================
# game variables
#===================================

GAME_STATE = STATE.SETUP

PLAYERS = []

SETUP_FUNCTIONS = {}
END_FUNCTIONS = {}
CHANCELLOR_FUNCTIONS = {}
VOTE_FUNCTIONS = {}
POLICY_FUNCTIONS = {}
ACTION_FUNCTIONS = {}
