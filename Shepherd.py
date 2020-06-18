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
    global CARD_DECK, GAME_STATE
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

def to_chancellor(args):
    """
    A function that moves the game into the chancellor phase.
    """
    global GAME_STATE
    GAME_STATE = STATE.CHANCELLOR
    ineligibles = {player_id(PRESIDENT_INDEX), player_id(PREVIOUS_PRESIDENT_INDEX), player_id(PREVIOUS_CHANCELLOR_INDEX)}
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "ineligibles": list(ineligibles)}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.CHANCELLOR_REQUEST, lcm_data)

def receive_chancellor_nomination(args):
    """
    A function that reads who the president has nominated for chancellor and
    starts the voting process.
    """
    global GAME_STATE, VOTES, NOMINATED_CHANCELLOR_INDEX
    GAME_STATE = STATE.VOTE
    VOTES = [0, 0]
    chancellor = args["nominee"]
    NOMINATED_CHANCELLOR_INDEX = player_ids(PLAYERS).index(chancellor)
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "chancellor": chancellor}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.AWAIT_VOTE, lcm_data)

def receive_vote(args):
    global VOTES, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX, ELECTION_TRACKER
    if args["vote"]:
        yes_vote()
    else:
        no_vote()
    if number_of_votes() >= len(PLAYERS):
        if passing_vote():
            PREVIOUS_PRESIDENT_INDEX = PRESIDENT_INDEX
            PREVIOUS_CHANCELLOR_INDEX = NOMINATED_CHANCELLOR_INDEX
            # TODO: handle if it passed
        else:
            ELECTION_TRACKER += 1
            if chaos():
                ELECTION_TRACKER = 0
                # TODO: handle the chaos
            PRESIDENT_INDEX = next_president_index()
            to_chancellor({})

#===================================
# helper functions
#===================================

def player_names(players):
    return [player.name for player in players]

def player_ids(players):
    return [player.id for player in players]

def player_id(index):
    return player_ids(PLAYERS)[index]

def reset():
    """
    Returns the game state to what it was at the beginning of executions
    """
    global PLAYERS, CARD_DECK, VOTES, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, ELECTION_TRACKER
    PLAYERS = []
    CARD_DECK = []
    VOTES = [0, 0]
    PRESIDENT_INDEX = 0
    PREVIOUS_PRESIDENT_INDEX = 0
    ELECTION_TRACKER = 0

def shuffle_deck(deck):
    random.shuffle(deck)

def new_deck():
    new_d = [CARDS.LIBERAL for _ in range(6)]
    new_d += [CARDS.FASCIST for _ in range(11)]
    shuffle_deck(new_d)
    return new_d

def next_president_index():
    global PRESIDENT_INDEX, PLAYERS
    return (PRESIDENT_INDEX + 1) % len(PLAYERS)

def yes_vote():
    global VOTES
    VOTES[0] += 1

def no_vote():
    global VOTES
    VOTES[1] += 1

def passing_vote():
    return VOTES[0] > VOTES[1]

def number_of_votes():
    return VOTES[0] + VOTES[1]

def chaos():
    return ELECTION_TRACKER == 3

#===================================
# game variables
#===================================

GAME_STATE = STATE.END

PLAYERS = []
CARD_DECK = []
VOTES = [0, 0] # [yes, no]
PRESIDENT_INDEX = 0
PREVIOUS_PRESIDENT_INDEX = 0 # for remembering who is ineligible
PREVIOUS_CHANCELLOR_INDEX = 0 # for remembering who is ineligible
NOMINATED_CHANCELLOR_INDEX = 0
ELECTION_TRACKER = 0

SETUP_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_new_game,
                   SHEPHERD_HEADERS.NEXT_STAGE : to_chancellor}
CHANCELLOR_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                        SHEPHERD_HEADERS.CHANCELLOR_NOMINATION : receive_chancellor_nomination}
VOTE_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                  SHEPHERD_HEADERS.PLAYER_VOTED : receive_vote}
POLICY_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
ACTION_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game}
END_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                 SHEPHERD_HEADERS.NEXT_STAGE : to_setup}
