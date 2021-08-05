
import queue
import random
from player import Player
from typing import List, Set, Dict, Tuple, Optional
from utils import *
from ydl import ydl_send, ydl_start_read
from board import Board
import time

# MAJOR TODOS:
# - literally all of javascript
# - what to send for reconnection in action state
# - do state transitions


# ===================================
# game variables
# ===================================


# the current game state (setup, pick chancellor, vote, policy, action, end)
GAME_STATE = STATE.SETUP

PLAYERS = {}  # a dictionary of ids -> Player objects representing the players in the game
SPECTATORS = {}  # a dictionary of ids -> Player objects representing the spectators
CARD_DECK = []  # the cards in the deck (not including discarded cards)
DISCARD_DECK = []  # the discarded cards
# the index of the president — this changes before the government is elected
PRESIDENT_ID = None
# the previous elected president (for remembering who is ineligible)
PREVIOUS_PRESIDENT_ID = None
# the previous elected chancellor (for remembering who is ineligible)
PREVIOUS_CHANCELLOR_ID = None
# the player who is nominated for chancellor
NOMINATED_CHANCELLOR_ID = None
# for remembering the president after a special election cycle, None if not a special election cycle
AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
FAILED_ELECTION_TRACKER = 0  # for tracking failed elections
BOARD = Board(5)  # the game board

# state specific variables

VOTE_PASSED = False # only valid in election_results state, says whether the vote passed
DRAWN_CARDS = [] # only valid in president_discard and chancellor discard states,
                 # cards that are up for discarding
CAN_VETO_THIS_ROUND = True # only valid in chancellor discard state
CURRENT_ACTION = None # only valid in the action state
CURRENT_INVESTIGATED_PLAYER = None # only valid in the action state
WINNER = None # only valid in end state; who the winner of the game is


def start():
    '''
    Main loop which processes the event queue and calls the appropriate function
    based on game state and the dictionary of available functions
    '''
    events = queue.Queue()
    ydl_start_read(YDL_TARGETS.SHEPHERD, events)
    while True:
        try:
            payload = events.get(True, timeout=1) #this timeout is required because windows is really stupid and terrible.
        except queue.Empty:
            continue
        print("GAME STATE OUTSIDE: ", GAME_STATE)
        print(payload)

        if GAME_STATE in FUNCTION_MAPPINGS:
            func_list = FUNCTION_MAPPINGS.get(GAME_STATE)
            func = func_list.get(payload[0]) or EVERYWHERE_FUNCTIONS.get(payload[0])
            if func is not None:
                func(**payload[1]) #deconstructs dictionary into arguments
            else:
                print(f"Invalid Event in {GAME_STATE}")
        else:
            print(f"Invalid State: {GAME_STATE}")

        print(diagnostics())



# ===================================
# game functions
# ===================================



def player_joined(id: str, name: str, secret: str):
    global PLAYERS

    all_names = [p.name for p in PLAYERS.values()] + \
                [p.name for p in SPECTATORS.values()]

    if id in PLAYERS:
        if PLAYERS[id].name != name or PLAYERS[id].secret != secret:
            ydl_send(*UI_HEADERS.BAD_LOGIN(
                message="Your login info was bad try again", 
                recipients=[id]
            ))
            return
    elif id in SPECTATORS:
        if SPECTATORS[id].name != name or SPECTATORS[id].secret != secret:
            ydl_send(*UI_HEADERS.BAD_LOGIN(
                message="Your login info was bad try again", 
                recipients=[id]
            ))
            return
    elif name in all_names:
        ydl_send(*UI_HEADERS.BAD_LOGIN(
            message="Somebody already took that name! Try again with a different name",
            recipients=[id]
        ))
        return
    else:
        if len(PLAYERS) >= 10 or GAME_STATE != STATE.SETUP: #TODO: remove hardcoding
            SPECTATORS[id] = Player(id, name, secret)
            SPECTATORS[id].role = ROLES.SPECTATOR
        else:
            PLAYERS[id] = Player(id, name, secret)

    ydl_send(*UI_HEADERS.ON_JOIN(
        usernames= [p.name for p in PLAYERS.values()],
        ids= [p.id for p in PLAYERS.values()],
        ongoing_game= GAME_STATE != STATE.SETUP,
    ))

    if GAME_STATE != STATE.SETUP:
        send_individual_setup(id)
        send_current_government(id)
        send_policies_enacted(id)
        send_failed_elections(id)

        # send state message
        send_funs = {
            STATE.SETUP: lambda _: None,
            STATE.VOTE: send_await_vote,
            STATE.ELECTION_RESULTS: send_election_results,
            STATE.PICK_CHANCELLOR: send_chancellor_request,
            STATE.PRESIDENT_DISCARD: send_president_discard,
            STATE.CHANCELLOR_DISCARD: send_chancellor_discard,
            STATE.CHANCELLOR_VETOED: send_ask_president_veto,
            STATE.ACTION: send_current_action,
            STATE.END: send_game_over
        }
        send_funs.get(GAME_STATE)(id)



def send_individual_setups():
    for p in PLAYERS:
        send_individual_setup(p)
    for p in SPECTATORS:
        send_individual_setup(p)

def send_individual_setup(id):
    p = None
    role = ROLES.SPECTATOR
    see_roles = False
    if id in PLAYERS:
        p = PLAYERS[id]
        role = p.role
        see_roles = role == ROLES.FASCIST or (role == ROLES.HITLER and len(PLAYERS) <= 6)
    player_roles = [[oth.name, oth.id, oth.role if see_roles or oth == p else ROLES.NONE]
        for oth in PLAYERS.values()]
    ydl_send(*UI_HEADERS.INDIVIDUAL_SETUP(
        roles=player_roles,
        individual_role=role,
        powers=BOARD.board,
        recipients=[id]
    ))


def to_setup():
    """
    A function that resets everything and moves the game into setup phase.
    """
    global PLAYERS; PLAYERS = {}
    global SPECTATORS; SPECTATORS = {}
    global CARD_DECK; CARD_DECK = []
    global DISCARD_DECK; DISCARD_DECK = []
    global PRESIDENT_ID; PRESIDENT_ID = None
    global PREVIOUS_PRESIDENT_ID; PREVIOUS_PRESIDENT_ID = None
    global PREVIOUS_CHANCELLOR_ID; PREVIOUS_CHANCELLOR_ID = None
    global NOMINATED_CHANCELLOR_ID; NOMINATED_CHANCELLOR_ID = None
    global AFTER_SPECIAL_ELECTION_PRESIDENT_ID; AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
    global FAILED_ELECTION_TRACKER; FAILED_ELECTION_TRACKER = 0
    global GAME_STATE; GAME_STATE = STATE.SETUP
    ydl_send(*UI_HEADERS.NEW_LOBBY())



def start_game():
    """
    A function that initializes variables that require the number of players.
    """
    global PLAYERS, BOARD, PRESIDENT_ID, CARD_DECK
    if len(PLAYERS) < 5:
        ydl_send(*UI_HEADERS.NOT_ENOUGH_PLAYERS(players=len(PLAYERS)))
        return

    PRESIDENT_ID = next_president_id()
    CARD_DECK = new_deck()

    # BEGIN QUESTION 1: initialize the list deck with 1 hitler and the relevant number of fascist and liberal cards. Hint: don't use raw strings to represent the roles. Instead, look for a useful class in Utils.py.
    # see the table on page 2 of the rules: https://secrethitler.com/assets/Secret_Hitler_Rules.pdf#page=2. For a challenge, try coming up with a formula for it.

    roles = [ROLES.HITLER]
    roles += [ROLES.FASCIST]*((len(PLAYERS)-3)//2)
    roles += [ROLES.LIBERAL]*(len(PLAYERS)//2 + 1)

    # END QUESTION 1
    shuffle_deck(roles)
    # BEGIN QUESTION 1
    # Assign roles for each player using the deck.
    player_objs = list(PLAYERS.values())
    for i in range(len(PLAYERS)):
        player_objs[i].role = roles[i]
    # Initialize the board.
    BOARD = Board(len(PLAYERS))
    # END QUESTION 1

    send_individual_setups()
    send_current_government()
    to_pick_chancellor()


def to_pick_chancellor():
    """
    A function that moves the game into the pick_chancellor phase. This is done
    by constructing a list of eligible players and sending the CHANCELLOR_REQUEST
    header to the server.
    """
    global GAME_STATE, NOMINATED_CHANCELLOR_ID
    GAME_STATE = STATE.PICK_CHANCELLOR
    NOMINATED_CHANCELLOR_ID = None
    send_current_government()
    # BEGIN QUESTION 3
    send_chancellor_request()
    # END QUESTION 3

def eligible_chancellor_nominees():
    """
    Returns the ids of players who can be nominated for chancellor
    Rules:
    - if there are > 5 players, the ineligible players are the president,
    previous president, and previous chancellor.
    - if <= 5 players, only the president and previous chancellor are ineligible
    """
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    remove_if_exists(eligibles, PREVIOUS_CHANCELLOR_ID)
    if len(PLAYERS) > 5:
        remove_if_exists(eligibles, PREVIOUS_PRESIDENT_ID)
    return eligibles


def receive_chancellor_nomination(secret, nominee):
    """
    A function that reads who the president has nominated for chancellor and
    starts the voting process.
    """
    global GAME_STATE, NOMINATED_CHANCELLOR_ID

    if bad_credentials(PRESIDENT_ID, secret): return

    GAME_STATE = STATE.VOTE
    NOMINATED_CHANCELLOR_ID = nominee
    send_current_government()
    send_await_vote()


def receive_vote(secret, id, vote):
    """
    A function that notes a vote and acts if the voting is done.
    """
    if bad_credentials(id, secret): return
    PLAYERS[id].vote = vote
    send_await_vote()
    if number_of_votes() >= len(PLAYERS):
        to_election_results()

def to_election_results():
    """
    updates VOTE_PASSED and the FAILED_ELECTION_TRACKER, then sends info to everyone
    """
    global GAME_STATE, VOTE_PASSED, FAILED_ELECTION_TRACKER
    GAME_STATE = STATE.ELECTION_RESULTS
    VOTE_PASSED = passing_vote()
    if not VOTE_PASSED: 
        FAILED_ELECTION_TRACKER += 1
    send_election_results()

def end_election_results(secret):
    """
    clears everyone's votes, then either advances to the next stage based on whether the
    vote has passed. May enact chaos.
    """
    global PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID, GAME_STATE, DRAWN_CARDS
    
    if bad_credentials(PRESIDENT_ID, secret): return
    
    for player in PLAYERS.values():
        player.clear_vote()

    if VOTE_PASSED:
        PREVIOUS_PRESIDENT_ID = PRESIDENT_ID
        PREVIOUS_CHANCELLOR_ID = NOMINATED_CHANCELLOR_ID
        # BEGIN QUESTION 4: if chancellor is hitler, and at least 3 fascist
        # policies have been enected,
        # game_over is called and the function is terminated

        if PLAYERS[NOMINATED_CHANCELLOR_ID].role == ROLES.HITLER and BOARD.fascist_enacted >= 3:
            game_over(ROLES.FASCIST)
            return

        # END QUESTION 4
        if len(CARD_DECK) < 3:
            reshuffle_deck()
        GAME_STATE = STATE.PRESIDENT_DISCARD
        DRAWN_CARDS = draw_cards(3)
        send_president_discard()
    else:
        if chaos(): 
            enact_chaos()
        advance_president()
        to_pick_chancellor()


def enact_chaos():
    """
    Throws the country into chaos. Resets the failed_election_tracker to 0,
    sets the previous president and chancellor to None, and enacts a random policy.
    """
    global FAILED_ELECTION_TRACKER, PREVIOUS_CHANCELLOR_ID, PREVIOUS_PRESIDENT_ID
    FAILED_ELECTION_TRACKER = 0
    send_failed_elections()
    if len(CARD_DECK) < 3:
        reshuffle_deck()
    card = draw_cards(1)[0]
    BOARD.enact_policy(card)
    PREVIOUS_PRESIDENT_ID = None
    PREVIOUS_CHANCELLOR_ID = None
    send_policies_enacted()


def president_discarded(secret, cards, discarded):
    """
    A function that takes the cards left and passes them to the chancellor.
    `cards` contains the remaining two cards.
    """
    global DISCARD_DECK, DRAWN_CARDS, GAME_STATE, CAN_VETO_THIS_ROUND

    if bad_credentials(PRESIDENT_ID, secret): return
    # BEGIN QUESTION 5
    GAME_STATE = STATE.CHANCELLOR_DISCARD
    DISCARD_DECK.append(discarded)
    DRAWN_CARDS = cards
    CAN_VETO_THIS_ROUND = BOARD.can_veto
    send_chancellor_discard()
    # END QUESTION 5


def chancellor_vetoed(secret):
    """
    A function that asks for the president's response after a chancellor veto.
    """
    global GAME_STATE

    if bad_credentials(NOMINATED_CHANCELLOR_ID, secret): return

    GAME_STATE = STATE.CHANCELLOR_VETOED
    send_ask_president_veto()


def president_veto_answer(secret: str, veto: bool):
    """
    A function that receives if the president vetoes or not.
    """
    global FAILED_ELECTION_TRACKER, GAME_STATE, CAN_VETO_THIS_ROUND
    
    if bad_credentials(PRESIDENT_ID, secret): return

    if veto:
        FAILED_ELECTION_TRACKER += 1
        send_failed_elections()
        if chaos():
            enact_chaos()
        advance_president()
        to_pick_chancellor()
    else:
        GAME_STATE = STATE.CHANCELLOR_DISCARD
        CAN_VETO_THIS_ROUND = False
        send_chancellor_discard()


def chancellor_discarded(secret, card, discarded):
    """
    A function that enacts the policy left over after two have been discarded.
    """
    global GAME_STATE, BOARD, PRESIDENT_ID, CURRENT_ACTION, \
        CURRENT_INVESTIGATED_PLAYER, FAILED_ELECTION_TRACKER

    if bad_credentials(NOMINATED_CHANCELLOR_ID, secret): return

    DISCARD_DECK.append(discarded)
    BOARD.enact_policy(card)
    FAILED_ELECTION_TRACKER = 0 # government has successfully enacted a policy
    DISCARD_DECK.append(card)
    send_failed_elections()
    send_policies_enacted()
    if BOARD.fascist_enacted >= 6:
        game_over(ROLES.FASCIST)
        return
    elif card == CARDS.LIBERAL or len(BOARD.current_power_list()) == 0:
        advance_president()
        to_pick_chancellor()
    else:
        GAME_STATE = STATE.ACTION
        CURRENT_INVESTIGATED_PLAYER = None
        for action in BOARD.current_power_list(): #TODO: sam does not like this model
            if action == POWERS.VETO:
                veto()
            else:
                CURRENT_ACTION = action
                send_current_action()


def send_current_action(id = None):
    send_functions = {
        POWERS.INVESTIGATE_LOYALTY: send_loyalty,
        POWERS.SPECIAL_ELECTION: call_special_election,
        POWERS.POLICY_PEEK: policy_peek,
        POWERS.EXECUTION: execution
    }
    send_functions[CURRENT_ACTION](id)


def send_loyalty(id = None):
    """
    A function that begins the Investigate Loyalty power. No player may be
    investigated twice in a game. Also resends headers if Investigate Loyalty
    is ongoing.
    """
    if CURRENT_INVESTIGATED_PLAYER is None:
        eligibles = [p for p in PLAYERS if not PLAYERS[p].investigated]
        if PRESIDENT_ID in eligibles:
            eligibles.remove(PRESIDENT_ID)
        ydl_send(*UI_HEADERS.BEGIN_INVESTIGATION(
            eligibles=eligibles,
            recipients=None if id is None else [id]
        ))
    else:
        role = PLAYERS[CURRENT_INVESTIGATED_PLAYER].role
        if role == ROLES.HITLER:
            role = ROLES.FASCIST
        if id is None or id == PRESIDENT_ID:
            ydl_send(*UI_HEADERS.RECEIVE_INVESTIGATION(
                player=CURRENT_INVESTIGATED_PLAYER,
                role=role,
                recipients=[PRESIDENT_ID]
            ))
        if id != PRESIDENT_ID:
            ydl_send(*UI_HEADERS.RECEIVE_INVESTIGATION(
                player=CURRENT_INVESTIGATED_PLAYER,
                role=ROLES.NONE,
                recipients=[p for p in PLAYERS if p != PRESIDENT_ID] \
                 if id is None else [id]
            ))


def investigate_player(secret, player):
    """
    A function that returns the loyalty (as a role) of the player the president
    has asked to investigate using the RECEIVE_INVESTIGATION header. Hitler
    is treated as a fascist.
    """
    # BEGIN QUESTION 6
    global CURRENT_INVESTIGATED_PLAYER
    if bad_id(player): return
    if bad_credentials(PRESIDENT_ID, secret): return 
    PLAYERS[player].investigated = True
    CURRENT_INVESTIGATED_PLAYER = player
    send_loyalty()

def call_special_election(id = None):
    """
    A function that begins the special election power.
    Send the appropriate header to the server with the correct data.
    Anyone except the current president is eligible to be the next president.
    """
    # BEGIN QUESTION 7
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    ydl_send(*UI_HEADERS.BEGIN_SPECIAL_ELECTION(
        eligibles=eligibles,
        recipients=None if id is None else [id]
    ))


def perform_special_election(secret, player):
    """
    A function that starts the next session with the new president.
    """
    global PRESIDENT_ID, AFTER_SPECIAL_ELECTION_PRESIDENT_ID
    if bad_id(player): return
    if bad_credentials(PRESIDENT_ID, secret): return
    AFTER_SPECIAL_ELECTION_PRESIDENT_ID = next_president_id()
    PRESIDENT_ID = player
    send_current_government()
    to_pick_chancellor()


def policy_peek(id = None):
    """
    A function that executes the policy peek power.
    """
    ydl_send(*UI_HEADERS.PERFORM_POLICY_PEEK(
        cards=CARD_DECK[:3],
        recipients=None if id is None else [id]
    ))


def end_policy_peek(secret: str):
    """
    A function that ends the policy peek.
    """
    if bad_credentials(PRESIDENT_ID, secret): return
    advance_president()
    to_pick_chancellor()


def end_investigate_player(secret: str):
    """
    A function that ends the investigate player.
    """
    if bad_credentials(PRESIDENT_ID, secret): return
    advance_president()
    to_pick_chancellor()


def execution(id = None):
    """
    A function that begins the execution power.
    """
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    ydl_send(*UI_HEADERS.BEGIN_EXECUTION(
        eligibles=eligibles,
        recipients=None if id is None else [id]
    ))


def perform_execution(secret, player: str):
    """
    A function that executes a player.
    """
    global PRESIDENT_ID, NOMINATED_CHANCELLOR_ID, PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID
    if bad_id(player): return
    if bad_credentials(PRESIDENT_ID, secret): return
    if PLAYERS[player].role == ROLES.HITLER:
        game_over(ROLES.LIBERAL)
        return
    player_obj = PLAYERS.pop(player)

    if player == PRESIDENT_ID: PRESIDENT_ID = None
    if player == NOMINATED_CHANCELLOR_ID: NOMINATED_CHANCELLOR_ID = None
    if player == PREVIOUS_PRESIDENT_ID: PREVIOUS_PRESIDENT_ID = None
    if player == PREVIOUS_CHANCELLOR_ID: PREVIOUS_CHANCELLOR_ID = None

    SPECTATORS[player] = player_obj
    advance_president() # also sends current government, in case chancellor dies
    ydl_send(*UI_HEADERS.PLAYER_EXECUTED(player=player))
    to_pick_chancellor()


def veto():
    """
    A function that turns on the veto power.
    """
    global BOARD
    BOARD.can_veto = True
    send_policies_enacted()


def game_over(winner):
    """
    A function that reports the end of a game.
    """
    global GAME_STATE, WINNER
    GAME_STATE = STATE.END
    WINNER = winner
    send_game_over()


# ===================================
# sender functions
# ===================================

def send_current_government(id = None):
    ydl_send(*UI_HEADERS.CURRENT_GOVERNMENT(
        president=PRESIDENT_ID,
        chancellor=NOMINATED_CHANCELLOR_ID,
        recipients=None if id is None else [id]
    ))

def send_policies_enacted(id = None):
    ydl_send(*UI_HEADERS.POLICIES_ENACTED(
        liberal=BOARD.liberal_enacted,
        fascist=BOARD.fascist_enacted,
        can_veto=BOARD.can_veto,
        recipients=None if id is None else [id]
    ))

def send_failed_elections(id = None):
    ydl_send(*UI_HEADERS.FAILED_ELECTIONS(
        num=FAILED_ELECTION_TRACKER,
        recipients=None if id is None else [id]
    ))

def send_chancellor_request(id = None):
    ydl_send(*UI_HEADERS.CHANCELLOR_REQUEST(
        eligibles=eligible_chancellor_nominees(),
        recipients=None if id is None else [id]
    ))

def send_await_vote(id = None):
    ydl_send(*UI_HEADERS.AWAIT_VOTE(
        has_voted=players_who_have_voted(),
        recipients=None if id is None else [id]
    ))

def send_election_results(id = None):
    ydl_send(*UI_HEADERS.ELECTION_RESULTS(
        voted_yes=players_who_have_voted(VOTES.JA),
        voted_no=players_who_have_voted(VOTES.NEIN),
        result=VOTE_PASSED,
        failed_elections=FAILED_ELECTION_TRACKER,
        recipients=None if id is None else [id]
    ))

def send_president_discard(id = None):
    if id is None or id == PRESIDENT_ID:
        ydl_send(*UI_HEADERS.PRESIDENT_DISCARD(
            cards=DRAWN_CARDS,
            recipients=[PRESIDENT_ID]
        ))
    if id != PRESIDENT_ID:
        ydl_send(*UI_HEADERS.PRESIDENT_DISCARD(
            cards=[], #for security, don't want other UIs to know cards
            recipients=[d for d in PLAYERS if d != PRESIDENT_ID]\
                if id is None else [id]
        ))

def send_chancellor_discard(id = None):
    if id is None or id == NOMINATED_CHANCELLOR_ID:
        ydl_send(*UI_HEADERS.CHANCELLOR_DISCARD(
            cards=DRAWN_CARDS,
            can_veto=CAN_VETO_THIS_ROUND,
            recipients=[NOMINATED_CHANCELLOR_ID]
        ))
    if id != NOMINATED_CHANCELLOR_ID:
        ydl_send(*UI_HEADERS.CHANCELLOR_DISCARD(
            cards=[], #for security, don't want other UIs to know cards
            can_veto=CAN_VETO_THIS_ROUND,
            recipients=[d for d in PLAYERS if d != NOMINATED_CHANCELLOR_ID]\
                if id is None else [id]
        ))

def send_ask_president_veto(id = None):
    ydl_send(*UI_HEADERS.ASK_PRESIDENT_VETO(
        recipients=None if id is None else [id]
    ))

def send_game_over(id = None):
    ydl_send(*UI_HEADERS.GAME_OVER(
        winner=WINNER,
        roles=[[p.name, p.id, p.role] for p in PLAYERS.values()],
        recipients=None if id is None else [id]
    ))

# ===================================
# helper functions
# ===================================

def bad_id(id):
    """
    Checks to make sure id is a valid id
    """
    if id not in PLAYERS:
        print(f"BAD ID: {id}")
        return True
    return False

def bad_credentials(id, secret):
    """
    Checks to make sure id is a valid id, and that the secret is correct
    """
    if bad_id(id):
        return True
    if PLAYERS[id].secret != secret:
        print(f"INCORRECT SECRET FOR {PLAYERS[id]}")
        return True
    return False


def remove_if_exists(ar, element):
    if element in ar:
        ar.remove(element)

def player_names(players):
    """
    Returns the list of player names
    """
    return [player.name for player in players]


def shuffle_deck(deck):
    """
    Shuffles a card deck
    """
    random.shuffle(deck)


def new_deck():
    """
    Returns a new full card deck with the appropriate cards
    """
    new_d = [CARDS.LIBERAL for _ in range(6)]
    new_d += [CARDS.FASCIST for _ in range(11)]
    shuffle_deck(new_d)
    return new_d


def reshuffle_deck():
    """
    Joins the discard pile with the rest of the card deck, then shuffles the card deck
    """
    global DISCARD_DECK, CARD_DECK
    discard_copy = DISCARD_DECK.copy()
    discard_copy.extend(CARD_DECK)
    CARD_DECK = discard_copy.copy()
    DISCARD_DECK = []
    shuffle_deck(CARD_DECK)


def draw_cards(number):
    """
    Draws and returns cards from the card deck
    """
    global CARD_DECK
    cards = []
    for i in range(number):
        cards.append(CARD_DECK.pop(0))
    return cards


def advance_president():
    global PRESIDENT_ID
    PRESIDENT_ID = next_president_id()
    send_current_government()


def next_president_id():
    """
    Gets the id of the next president, taking into account special elections
    """
    global AFTER_SPECIAL_ELECTION_PRESIDENT_ID
    if AFTER_SPECIAL_ELECTION_PRESIDENT_ID != None:
        value = AFTER_SPECIAL_ELECTION_PRESIDENT_ID
        AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
        return value
    all_ids = list(PLAYERS)
    if PRESIDENT_ID in all_ids:
        ind = (all_ids.index(PRESIDENT_ID) + 1) % len(all_ids)
        return all_ids[ind]
    else:
        return all_ids[0]



def number_of_votes():
    """
    Returns the number of players that recorded votes
    """
    return len(players_who_have_voted())

def players_who_have_voted(vote=None):
    """
    Returns the ids of players who have voted
    """
    if vote is None:
        return [p.id for p in PLAYERS.values() if p.vote != VOTES.UNDEFINED]
    else:
        return [p.id for p in PLAYERS.values() if p.vote == vote]


def passing_vote():
    """
    Returns if the recorded votes would elect the proposed government
    """
    diff = 0
    for player in PLAYERS.values():
        if player.vote == VOTES.JA:
            diff += 1
        else:
            diff -= 1
    return diff > 0


def chaos():
    """
    Returns if the country should be thrown into chaos
    """
    return FAILED_ELECTION_TRACKER == 3


def diagnostics():
    """
    Returns information about the current game
    """
    diag = "Diagnostics:"
    diag += "\n\tState: " + GAME_STATE
    diag += "\n\tPlayers: " + str([str(p) for p in PLAYERS.values()])
    diag += "\n\tSpectators: " + str([str(s) for s in SPECTATORS.values()])
    diag += "\n\tPresident: " + str(PLAYERS.get(PRESIDENT_ID, None))
    diag += "\n\tNominated Chancellor: " + str(PLAYERS.get(NOMINATED_CHANCELLOR_ID, None))
    diag += "\n\tPrevious President: " + str(PLAYERS.get(PREVIOUS_PRESIDENT_ID, None))
    diag += "\n\tPrevious Chancellor: " + str(PLAYERS.get(PREVIOUS_CHANCELLOR_ID, None))
    diag += "\n\tElection Tracker: " + str(FAILED_ELECTION_TRACKER)
    diag += "\n\tLiberal Enacted: " + str(BOARD.liberal_enacted)
    diag += "\n\tFascist Enacted: " + str(BOARD.fascist_enacted)
    diag += "\n\tCard Deck: " + str(CARD_DECK)
    return diag




###########################################
# Event to Function Mappings for each Stage
###########################################

FUNCTION_MAPPINGS = {
    STATE.SETUP: {
        SHEPHERD_HEADERS.PLAYER_JOINED.name: player_joined,
        SHEPHERD_HEADERS.NEXT_STAGE.name: start_game
    },
    STATE.VOTE: {
        SHEPHERD_HEADERS.PLAYER_VOTED.name: receive_vote
    },
    STATE.ELECTION_RESULTS: {
        SHEPHERD_HEADERS.END_ELECTION_RESULTS.name: end_election_results
    },
    STATE.PICK_CHANCELLOR: {
        SHEPHERD_HEADERS.CHANCELLOR_NOMINATION.name: receive_chancellor_nomination
    },
    STATE.PRESIDENT_DISCARD: {
        SHEPHERD_HEADERS.PRESIDENT_DISCARDED.name: president_discarded
    },
    STATE.CHANCELLOR_DISCARD: {
        SHEPHERD_HEADERS.CHANCELLOR_DISCARDED.name: chancellor_discarded,
        SHEPHERD_HEADERS.CHANCELLOR_VETOED.name: chancellor_vetoed,
    },
    STATE.CHANCELLOR_VETOED: {
        SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER.name: president_veto_answer,
    },
    STATE.ACTION: {
        SHEPHERD_HEADERS.INVESTIGATE_PLAYER.name: investigate_player,
        SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK.name: perform_special_election,
        SHEPHERD_HEADERS.PERFORM_EXECUTION.name: perform_execution,
        SHEPHERD_HEADERS.END_POLICY_PEEK.name: end_policy_peek,
        SHEPHERD_HEADERS.END_INVESTIGATE_PLAYER.name: end_investigate_player
    },
    STATE.END: {
        SHEPHERD_HEADERS.NEXT_STAGE.name: to_setup
    }
}

EVERYWHERE_FUNCTIONS = {
    SHEPHERD_HEADERS.PLAYER_JOINED.name: player_joined,
}

if __name__ == '__main__':
    start()
