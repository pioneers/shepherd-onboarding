
import queue
import random
from player import Player
from typing import List, Set, Dict, Tuple, Optional
from utils import *
from ydl import ydl_send, ydl_start_read
from board import Board
import time

# MAJOR TODOS:
# - javascript cookies -> uri compnents ofc
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
# for remembering the president after a special election cycle, Player.NONE if not a special election cycle
AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
FAILED_ELECTION_TRACKER = 0  # for tracking failed elections
BOARD = Board(5)  # the game board

DRAWN_CARDS = [] # only valid in president_discard and chancellor discard states,
                 # cards that are up for discarding
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



def player_joined(id: str, name: str):
    global PLAYERS

    if id not in PLAYERS and id not in SPECTATORS:
        if len(PLAYERS) >= 10 or GAME_STATE != STATE.SETUP: #TODO: remove hardcoding
            SPECTATORS[id] = Player(id, name)
            SPECTATORS[id].role = ROLES.SPECTATOR
        else:
            PLAYERS[id] = Player(id, name)

    all_players = list(PLAYERS.values()) + list(SPECTATORS.values())
    ydl_send(*UI_HEADERS.ON_JOIN(
        usernames= [p.name for p in all_players],
        ids= [p.id for p in all_players],
        ongoing_game= GAME_STATE != STATE.SETUP,
    ))

    if GAME_STATE != STATE.SETUP:
        send_individual_setup(id)
        send_policies_enacted(id)

        # send state message
        send_state = {
            STATE.SETUP: None,
            STATE.VOTE: lambda: UI_HEADERS.AWAIT_VOTE(
                president=PRESIDENT_ID,
                chancellor=NOMINATED_CHANCELLOR_ID,
                has_voted=players_who_have_voted(),
                recipients=[id]
            ),
            STATE.PICK_CHANCELLOR: lambda: UI_HEADERS.CHANCELLOR_REQUEST(
                president=PRESIDENT_ID,
                eligibles=eligible_chancellor_nominees(),
                recipients=[id]
            ),
            STATE.PRESIDENT_DISCARD: lambda: UI_HEADERS.PRESIDENT_DISCARD(
                president=PRESIDENT_ID,
                cards=DRAWN_CARDS,
                recipients=[id]
            ),
            STATE.CHANCELLOR_DISCARD: lambda: UI_HEADERS.CHANCELLOR_DISCARD(
                chancellor=NOMINATED_CHANCELLOR_ID,
                cards=DRAWN_CARDS,
                can_veto=BOARD.can_veto,
                recipients=[id]
            ),
            STATE.CHANCELLOR_VETOED: lambda: UI_HEADERS.ASK_PRESIDENT_VETO(
                president=PRESIDENT_ID,
                recipients=[id]
            ),
            STATE.ACTION: None, # TODO
            STATE.END: lambda: UI_HEADERS.GAME_OVER(
                winner=WINNER,
                recipients=[id]
            )
        }.get(GAME_STATE)
        if send_state is not None:
            ydl_send(*send_state())



def send_individual_setups():
    for p in PLAYERS:
        send_individual_setup(p)
    for p in SPECTATORS:
        send_individual_setup(p)

def send_individual_setup(id):
    p = None
    role = ROLES.SPECTATOR
    see_roles = True
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
    ydl_send(*UI_HEADERS.FORCE_RECONNECT())



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
    to_pick_chancellor()


def to_pick_chancellor():
    """
    A function that moves the game into the pick_chancellor phase. This is done
    by constructing a list of eligible players and sending the CHANCELLOR_REQUEST
    header to the server.
    """
    global GAME_STATE
    GAME_STATE = STATE.PICK_CHANCELLOR
    # BEGIN QUESTION 3
    ydl_send(*UI_HEADERS.CHANCELLOR_REQUEST(
        president=PRESIDENT_ID,
        eligibles=eligible_chancellor_nominees()
    ))
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


def receive_chancellor_nomination(nominee):
    """
    A function that reads who the president has nominated for chancellor and
    starts the voting process.
    """
    global GAME_STATE, NOMINATED_CHANCELLOR_ID
    GAME_STATE = STATE.VOTE
    NOMINATED_CHANCELLOR_ID = nominee
    ydl_send(*UI_HEADERS.AWAIT_VOTE(
        president=PRESIDENT_ID,
        chancellor=NOMINATED_CHANCELLOR_ID,
        has_voted=players_who_have_voted()
    ))


def receive_vote(id, vote):
    """
    A function that notes a vote and acts if the voting is done.
    """
    global GAME_STATE, PRESIDENT_ID, PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID, FAILED_ELECTION_TRACKER, CARD_DECK, DRAWN_CARDS
    PLAYERS[id].vote = vote
    if number_of_votes() >= len(PLAYERS):
        passed = passing_vote()
        for player in PLAYERS.values():
            player.clear_vote()
        if passed:
            PREVIOUS_PRESIDENT_ID = PRESIDENT_ID
            PREVIOUS_CHANCELLOR_ID = NOMINATED_CHANCELLOR_ID
            # BEGIN QUESTION 4: if chancellor is hitler, and at least 3 fascist
            # policies have been enected,
            # game_over is called and the function is terminated

            FAILED_ELECTION_TRACKER = 0
            if PLAYERS[NOMINATED_CHANCELLOR_ID].role == ROLES.HITLER and BOARD.fascist_enacted >= 3:
                game_over(ROLES.FASCIST)
                return

            # END QUESTION 4
            if len(CARD_DECK) < 3:
                reshuffle_deck()
            GAME_STATE = STATE.PRESIDENT_DISCARD
            DRAWN_CARDS = draw_cards(3)
            ydl_send(*UI_HEADERS.PRESIDENT_DISCARD(
                president=PRESIDENT_ID,
                cards=DRAWN_CARDS
            ))
        else:
            FAILED_ELECTION_TRACKER += 1
            if chaos():
                FAILED_ELECTION_TRACKER = 0
                if len(CARD_DECK) < 3:
                    reshuffle_deck()
                card = draw_cards(1)[0]
                BOARD.enact_policy(card)
                PREVIOUS_PRESIDENT_ID = Player.NONE
                PREVIOUS_CHANCELLOR_ID = Player.NONE
                send_policies_enacted()
            PRESIDENT_ID = next_president_id()
            to_pick_chancellor()


def president_discarded(cards, discarded):
    """
    A function that takes the cards left and passes them to the chancellor.
    `cards` contains the remaining two cards.
    """
    global DISCARD_DECK, DRAWN_CARDS, GAME_STATE
    # BEGIN QUESTION 5
    GAME_STATE = STATE.CHANCELLOR_DISCARD
    DISCARD_DECK.append(discarded)
    DRAWN_CARDS = cards
    ydl_send(*UI_HEADERS.CHANCELLOR_DISCARD(
        chancellor=NOMINATED_CHANCELLOR_ID,
        cards=DRAWN_CARDS,
        can_veto=BOARD.can_veto
    ))
    # END QUESTION 5


def chancellor_vetoed():
    """
    A function that asks for the president's response after a chancellor veto.
    """
    global GAME_STATE
    GAME_STATE = STATE.CHANCELLOR_VETOED
    ydl_send(*UI_HEADERS.ASK_PRESIDENT_VETO(president=PRESIDENT_ID))


def president_veto_answer(veto: bool, cards: List[str]):
    """
    A function that receives if the president vetoes or not.
    """
    global FAILED_ELECTION_TRACKER, PRESIDENT_ID, PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID, CARD_DECK, GAME_STATE
    if veto:
        FAILED_ELECTION_TRACKER += 1
        if chaos():
            FAILED_ELECTION_TRACKER = 0
            if len(CARD_DECK) < 3:
                reshuffle_deck()
            card = draw_cards(1)[0]
            BOARD.enact_policy(card)
            PREVIOUS_PRESIDENT_ID = Player.NONE
            PREVIOUS_CHANCELLOR_ID = Player.NONE
            send_policies_enacted()
        PRESIDENT_ID = next_president_id()
        to_pick_chancellor()
    else:
        GAME_STATE = STATE.CHANCELLOR_DISCARD
        ydl_send(*UI_HEADERS.CHANCELLOR_DISCARD(
            chancellor=NOMINATED_CHANCELLOR_ID,
            cards=cards, can_veto=BOARD.can_veto
        ))


def chancellor_discarded(card, discarded):
    """
    A function that enacts the policy left over after two have been discarded.
    """
    global GAME_STATE, BOARD, PRESIDENT_ID
    DISCARD_DECK.append(discarded)
    BOARD.enact_policy(card)
    DISCARD_DECK.append(card)
    send_policies_enacted()
    if BOARD.fascist_enacted >= 6:
        game_over(ROLES.FASCIST)
        return
    elif card == CARDS.LIBERAL or len(BOARD.current_power_list()) == 0:
        PRESIDENT_ID = next_president_id()
        to_pick_chancellor()
    else:
        GAME_STATE = STATE.ACTION
        for action in BOARD.current_power_list():
            if action == POWERS.INVESTIGATE_LOYALTY:
                investigate_loyalty()
            elif action == POWERS.SPECIAL_ELECTION:
                call_special_election()
            elif action == POWERS.POLICY_PEEK:
                policy_peek()
                PRESIDENT_ID = next_president_id()
            elif action == POWERS.EXECUTION:
                execution()
            elif action == POWERS.VETO:
                veto()
                PRESIDENT_ID = next_president_id()


def investigate_loyalty():
    """
    A function that begins the Investigate Loyalty power.
    """
    eligibles = [p for p in PLAYERS if not PLAYERS[p].investigated]
    ydl_send(*UI_HEADERS.BEGIN_INVESTIGATION(
        president=PRESIDENT_ID,
        eligibles=eligibles
    ))


def investigate_player(player):
    """
    A function that returns the loyalty (as a role) of the player the president
    has asked to investigate using the RECEIVE_INVESTIGATION header. Hitler
    is treated as a fascist.
    """
    # BEGIN QUESTION 6
    PLAYERS[player].investigated = True
    role = PLAYERS[player].role
    if role == ROLES.HITLER:
        role = ROLES.FASCIST
    # find out the loyalty and send it to the server.
    ydl_send(*UI_HEADERS.RECEIVE_INVESTIGATION(
        president=PRESIDENT_ID,
        role=role
    ))

def call_special_election():
    """
    A function that begins the special election power.
    Send the appropriate header to the server with the correct data.
    Anyone except the current president is eligible to be the next president.
    """
    # BEGIN QUESTION 7
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    ydl_send(*UI_HEADERS.BEGIN_SPECIAL_ELECTION(
        president=PRESIDENT_ID,
        eligibles=eligibles
    ))


def perform_special_election(player):
    """
    A function that starts the next session with the new president.
    """
    global PRESIDENT_ID, AFTER_SPECIAL_ELECTION_PRESIDENT_ID
    AFTER_SPECIAL_ELECTION_PRESIDENT_ID = next_president_id()
    PRESIDENT_ID = player
    to_pick_chancellor()


def policy_peek():
    """
    A function that executes the policy peek power.
    """
    ydl_send(*UI_HEADERS.PERFORM_POLICY_PEEK(
        president=PRESIDENT_ID,
        cards=CARD_DECK[:3]
    ))


def end_policy_peek():
    """
    A function that ends the policy peek.
    """
    to_pick_chancellor()


def end_investigate_player():
    """
    A function that ends the investigate player.
    """
    global PRESIDENT_ID
    PRESIDENT_ID = next_president_id()
    to_pick_chancellor()


def execution():
    """
    A function that begins the execution power.
    """
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    ydl_send(*UI_HEADERS.BEGIN_EXECUTION(
        president=PRESIDENT_ID,
        eligibles=eligibles
    ))


def perform_execution(player: str):
    """
    A function that executes a player.
    """
    global PRESIDENT_ID, NOMINATED_CHANCELLOR_ID, PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID
    if PLAYERS[player].role == ROLES.HITLER:
        game_over(ROLES.LIBERAL)
        return
    PLAYERS.pop(player)

    if player == PRESIDENT_ID: PRESIDENT_ID = None
    if player == NOMINATED_CHANCELLOR_ID: NOMINATED_CHANCELLOR_ID = None
    if player == PREVIOUS_PRESIDENT_ID: PREVIOUS_PRESIDENT_ID = None
    if player == PREVIOUS_CHANCELLOR_ID: PREVIOUS_CHANCELLOR_ID = None

    SPECTATORS.append(player)
    PRESIDENT_ID = next_president_id()
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
    ydl_send(*UI_HEADERS.GAME_OVER(winner=winner))


# ===================================
# sender functions
# ===================================

def send_policies_enacted(id = None):
    if id is None:
        ydl_send(*UI_HEADERS.POLICIES_ENACTED(
            liberal=BOARD.liberal_enacted,
            fascist=BOARD.fascist_enacted,
            can_veto=BOARD.can_veto
        ))
    else:
        ydl_send(*UI_HEADERS.POLICIES_ENACTED(
            liberal=BOARD.liberal_enacted,
            fascist=BOARD.fascist_enacted,
            can_veto=BOARD.can_veto,
            recipients=[id]
        ))

# ===================================
# helper functions
# ===================================

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

def players_who_have_voted():
    """
    Returns the ids of players who have voted
    """
    return [p.id for p in PLAYERS.values() if p.vote != VOTES.UNDEFINED]


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
