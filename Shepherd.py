from Player import Player
from Utils import *
from LCM import *
import random

def LCM_receive(header, dic={}):
    """
    this dispatches LCM requests from the server in a way that mimics the
    asynchronous dispatching that normally happens in shepherd
    """
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

def to_setup(args):
    """
    A function that moves the game into setup phase.
    """
    reset()
    CARD_DECK = new_deck()
    GAME_STATE = STATE.SETUP
    # this needs to be the last thing that happens, since due to how this
    # pseudo-LCM actually works, this will do a signifigant amount of work on
    # the server's side, and may spawn more LCM messages.
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.FORCE_RECONNECT, {})


def player_joined_new_game(args):
    """
    A function that creates a new player instance for a player who has joined,
    or will allow a player to reconnect if they have joined before.
    """
    global PLAYERS
    id = args["id"]
    name = args["name"]
    lcm_data = {"usernames" : player_names(PLAYERS)}
    if not id in player_ids(PLAYERS):
        # is this someone reconnecting or joining for the first time?
        PLAYERS += [Player(id, name)]
        lcm_data["recipients"] = player_ids(PLAYERS)
    else:
        lcm_data["recipients"] = [id]
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.PLAYERS, lcm_data)

def player_joined_ongoing_game(args):
    """
    A function that allows players to reconnect to the game.
    """
    global PLAYERS
    id = args["id"]
    name = args["name"]
    if id in player_ids(PLAYERS):
        # is this someone reconnecting or joining for the first time?
        lcm_data = {"usernames" : player_names(PLAYERS), "recipients" : [id]}
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.PLAYERS, lcm_data)
        # TODO: there is more stuff to send to the player probably

#===================================
# helper functions
#===================================

def player_names(players):
    return [player.name for player in players]

def player_ids(players):
    return [player.id for player in players]

def reset():
    """
    Retuns the game state to what it was at the begining of executions
    """
    PLAYERS = []
    CARD_DECK = []
    PLAYER_INDEX = 0
    PREVIOUS_PLAYER_INDEX = 0
    ELECTION_TRACKER = 0

def shuffle_deck(deck):
    random.shuffle(deck)

def new_deck():
    new_deck = [CARDS.LIBERAL for _ in range(6)]
    new_deck += [CARDS.FASCIST for _ in range(11)]
    shuffle_deck(new_deck)
    return new_deck

def next_player_index():
    global PLAYER_INDEX, PLAYERS
    return (PLAYER_INDEX + 1) % len(PLAYERS)

#===================================
# game variables
#===================================

GAME_STATE = STATE.END

PLAYERS = []
CARD_DECK = []
PLAYER_INDEX = 0
PREVIOUS_PLAYER_INDEX = 0
ELECTION_TRACKER = 0

SETUP_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_new_game}
CHANCELLOR_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
VOTE_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
POLICY_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
ACTION_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
END_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                 SHEPHERD_HEADERS.NEXT_STAGE : to_setup}
