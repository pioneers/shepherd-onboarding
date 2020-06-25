from Player import Player
from Utils import *
from LCM import *
from Board import Board
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
        if func:
            func(dic)
        else:
            print("Invalid Event in Setup")
    elif GAME_STATE == STATE.END:
        func = END_FUNCTIONS.get(header)
        if func:
            func(dic)
        else:
            print("Invalid Event in End")
    elif GAME_STATE == STATE.PICK_CHANCELLOR:
        func = CHANCELLOR_FUNCTIONS.get(header)
        if func:
            func(dic)
        else:
            print("Invalid Event in Pick Chancellor")
    elif GAME_STATE == STATE.VOTE:
        func = VOTE_FUNCTIONS.get(header)
        if func:
            func(dic)
        else:
            print("Invalid Event in Vote")
    elif GAME_STATE == STATE.POLICY:
        func = POLICY_FUNCTIONS.get(header)
        if func:
            func(dic)
        else:
            print("Invalid Event in Policy")
    elif GAME_STATE == STATE.ACTION:
        func = ACTION_FUNCTIONS.get(header)
        if func:
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

def start_game(args):
    """
    A function that initializes variables that require the number of players.
    """
    global PLAYERS, BOARD
    if len(PLAYERS) < 5:
        #TODO notify clients that there are not enough players.
        return
    deck = [ROLES.LIBERAL] * (len(PLAYERS) // 2 + 1)
    deck += [ROLES.FASCIST] * ((len(PLAYERS) - 1) // 2 - 1)
    deck += [ROLES.HITLER]
    shuffle_deck(deck)
    for i in range(len(PLAYERS)):
        PLAYERS[i].role = deck[i]
    BOARD = Board(len(PLAYERS))
    to_chancellor()

def to_chancellor():
    """
    A function that moves the game into the chancellor phase.
    """
    global GAME_STATE
    GAME_STATE = STATE.PICK_CHANCELLOR
    ineligibles = {player_id(PRESIDENT_INDEX), player_id(PREVIOUS_PRESIDENT_INDEX), player_id(PREVIOUS_CHANCELLOR_INDEX)}
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "ineligibles": list(ineligibles)}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.CHANCELLOR_REQUEST, lcm_data)

def receive_chancellor_nomination(args):
    """
    A function that reads who the president has nominated for chancellor and
    starts the voting process.
    """
    global GAME_STATE, NOMINATED_CHANCELLOR_INDEX
    GAME_STATE = STATE.VOTE
    chancellor = args["nominee"]
    NOMINATED_CHANCELLOR_INDEX = player_ids(PLAYERS).index(chancellor)
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "chancellor": chancellor}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.AWAIT_VOTE, lcm_data)

def receive_vote(args):
    """
    A function that notes a vote and acts if the voting is done.
    """
    global GAME_STATE, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX, ELECTION_TRACKER, CARD_DECK
    player = player_for_id(args["id"])
    player.vote = args["vote"]
    if number_of_votes() >= len(PLAYERS):
        passed = passing_vote()
        for player in PLAYERS:
            player.clear_vote()
        if passed:
            PREVIOUS_PRESIDENT_INDEX = PRESIDENT_INDEX
            PREVIOUS_CHANCELLOR_INDEX = NOMINATED_CHANCELLOR_INDEX
            if PLAYERS[NOMINATED_CHANCELLOR_INDEX].role == ROLES.HITLER and BOARD.fascist_enacted >= 3:
                print("Game over") # TODO: game over
            if len(CARD_DECK) < 3:
                CARD_DECK = DISCARD_DECK.copy().append(CARD_DECK)
                shuffle_deck(CARD_DECK)
            GAME_STATE = STATE.POLICY
            lcm_data = {"cards": draw_cards(3)}
            lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.PRESIDENT_DISCARD, lcm_data)
        else:
            ELECTION_TRACKER += 1
            if chaos():
                ELECTION_TRACKER = 0
                if len(CARD_DECK) < 3:
                    CARD_DECK = DISCARD_DECK.copy().append(CARD_DECK)
                    shuffle_deck(CARD_DECK)
                card = draw_cards(1)[0]
                BOARD.enact_policy(card)
            PRESIDENT_INDEX = next_president_index()
            to_chancellor()

def president_discarded(args):
    """
    A function that takes the policies left and passes them to the chancellor.
    """
    global DISCARD_DECK
    cards = args["cards"]
    discarded = args["discarded"]
    DISCARD_DECK.append(discarded)
    lcm_data = {"cards": cards, "can_veto": BOARD.can_veto}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.CHANCELLOR_DISCARD, lcm_data)

def chancellor_vetoed(args):
    """
    A function that asks for the president's response after a chancellor veto.
    """
    lcm_data = {"president": player_id(PRESIDENT_INDEX)}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.ASK_PRESIDENT_VETO, lcm_data)

def president_veto_answer(args):
    """
    A function that receives if the president vetoes or not.
    """
    global ELECTION_TRACKER, PRESIDENT_INDEX
    value = args["veto"]
    if value:
        ELECTION_TRACKER += 1
        if chaos():
            ELECTION_TRACKER = 0
            # TODO: handle the chaos
        PRESIDENT_INDEX = next_president_index()
        to_chancellor()
    else:
        president_discarded({"cards": args["cards"]})

def chancellor_discarded(args):
    """
    A function that enacts the policy left over after two have been discarded.
    """
    global GAME_STATE, BOARD, PRESIDENT_INDEX
    card = args["card"]
    discarded = args["discarded"]
    DISCARD_DECK.append(discarded)
    BOARD.enact_policy(card)
    lcm_data = {"liberal": BOARD.liberal_enacted, "fascist": BOARD.fascist_enacted}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.POLICIES_ENACTED, lcm_data)
    if BOARD.fascist_enacted >= 6:
        print("Game over") # TODO: game over
    elif card == CARDS.LIBERAL or len(BOARD.current_power_list()) == 0:
        PRESIDENT_INDEX = next_president_index()
        to_chancellor()
    else:
        GAME_STATE = STATE.ACTION
        for action in BOARD.current_power_list():
            if action == POWERS.INVESTIGATE_LOYALTY:
                investigate_loyalty()
                PRESIDENT_INDEX = next_president_index()
            elif action == POWERS.SPECIAL_ELECTION:
                call_special_election()
            elif action == POWERS.POLICY_PEEK:
                policy_peek()
                PRESIDENT_INDEX = next_president_index()
            elif action == POWERS.EXECUTION:
                execution()
                PRESIDENT_INDEX = next_president_index()
            elif action == POWERS.VETO:
                veto()
                PRESIDENT_INDEX = next_president_index()
        to_chancellor()

def investigate_loyalty():
    """
    A function that begins the Investigate Loyalty power.
    """
    investigated = [player_id(i) for i in range(len(PLAYERS)) if not PLAYERS[i].investigated]
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "previous": investigated}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.BEGIN_INVESTIGATION, lcm_data)

def investigate_player(args):
    """
    A function that returns the loyalty (as a role) of the player the president
    has asked to investigate.
    """
    player = player_for_id(args["player"])
    loyalty = ROLES.LIBERAL if player.role == ROLES.LIBERAL else ROLES.FASCIST
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "loyalty": loyalty}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.RECEIVE_INVESTIGATION, lcm_data)

def call_special_election():
    """
    A function that begins the special election power.
    """
    lcm_data = {"president": player_id(PRESIDENT_INDEX)}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.BEGIN_SPECIAL_ELECTION, lcm_data)

def perform_special_election(args):
    """
    A function that starts the next session with the new president.
    """
    global PRESIDENT_INDEX, AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX
    AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = next_president_index()
    PRESIDENT_INDEX = player_ids(PLAYERS).index(args["player"])
    to_chancellor()

def policy_peek():
    """
    A function that executes the policy peek power.
    """
    cards = [CARD_DECK[i] for i in range(min(len(CARD_DECK), 3))]
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "cards": cards}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.PERFORM_POLICY_PEEK, lcm_data)

def execution():
    """
    A function that begins the execution power.
    """
    lcm_data = {"president": player_id(PRESIDENT_INDEX)}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.BEGIN_EXECUTION, lcm_data)

def perform_execution(args):
    """
    A function that executes a player.
    """
    p_id = args["player"]
    player = player_for_id(p_id)
    if player.role == ROLES.HITLER:
        print("Game over") # TODO: game over
    del PLAYERS[player_ids(PLAYERS).index(p_id)]

def veto():
    """
    A function that turns on the veto power.
    """
    global BOARD
    BOARD.can_veto = True

#===================================
# helper functions
#===================================

def player_names(players):
    return [player.name for player in players]

def player_ids(players):
    return [player.id for player in players]

def player_id(index):
    return player_ids(PLAYERS)[index]

def player_for_id(p_id):
    return PLAYERS[player_ids(PLAYERS).index(p_id)]

def reset():
    """
    Returns the game state to what it was at the beginning of executions
    """
    global PLAYERS, CARD_DECK, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX, NOMINATED_CHANCELLOR_INDEX, AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX, ELECTION_TRACKER
    PLAYERS = []
    CARD_DECK = []
    DISCARD_DECK = []
    PRESIDENT_INDEX = 0
    PREVIOUS_PRESIDENT_INDEX = 0
    PREVIOUS_CHANCELLOR_INDEX = 0
    NOMINATED_CHANCELLOR_INDEX = 0
    AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = -1
    ELECTION_TRACKER = 0

def shuffle_deck(deck):
    random.shuffle(deck)

def new_deck():
    new_d = [CARDS.LIBERAL for _ in range(6)]
    new_d += [CARDS.FASCIST for _ in range(11)]
    shuffle_deck(new_d)
    return new_d

def draw_cards(number):
    global CARD_DECK
    cards = []
    for i in range(number):
        cards.append(CARD_DECK.pop(0))
    return cards

def next_president_index():
    global AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX
    if AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX != -1:
        value = AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX
        AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = -1
        return value
    return (PRESIDENT_INDEX + 1) % len(PLAYERS)

def number_of_votes():
    votes = 0
    for player in PLAYERS:
        if player.vote != VOTES.UNDEFINED:
            votes += 1
    return votes

def passing_vote():
    diff = 0
    for player in PLAYERS:
        if player.vote == VOTES.JA:
            diff += 1
        else:
            diff -= 1
    return diff > 0

def chaos():
    return ELECTION_TRACKER == 3

#===================================
# game variables
#===================================

GAME_STATE = STATE.END

PLAYERS = []
CARD_DECK = []
PRESIDENT_INDEX = 0
PREVIOUS_PRESIDENT_INDEX = 0 # for remembering who is ineligible
PREVIOUS_CHANCELLOR_INDEX = 0 # for remembering who is ineligible
NOMINATED_CHANCELLOR_INDEX = 0
AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = -1 # for remembering the president after a special election cycle, -1 if not a special election cycle
ELECTION_TRACKER = 0
BOARD = Board(5)

SETUP_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_new_game,
                   SHEPHERD_HEADERS.NEXT_STAGE : start_game}
CHANCELLOR_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                        SHEPHERD_HEADERS.CHANCELLOR_NOMINATION : receive_chancellor_nomination}
VOTE_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                  SHEPHERD_HEADERS.PLAYER_VOTED : receive_vote}
POLICY_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                    SHEPHERD_HEADERS.PRESIDENT_DISCARDED : president_discarded,
                    SHEPHERD_HEADERS.CHANCELLOR_DISCARDED : chancellor_discarded,
                    SHEPHERD_HEADERS.CHANCELLOR_VETOED : chancellor_vetoed,
                    SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER : president_veto_answer}
ACTION_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                    SHEPHERD_HEADERS.INVESTIGATE_PLAYER : investigate_player,
                    SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK : perform_special_election,
                    SHEPHERD_HEADERS.PERFORM_EXECUTION : perform_execution}
END_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED : player_joined_ongoing_game,
                 SHEPHERD_HEADERS.NEXT_STAGE : to_setup}
