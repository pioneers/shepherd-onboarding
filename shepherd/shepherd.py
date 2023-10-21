
import queue
import random
from player import Player
from typing import List, Set, Dict, Tuple, Optional
from utils import *
from ydl import Client, Handler
from board import Board
import time


YC = Client(YDL_TARGETS.SHEPHERD)

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
# the player who is nominated ffdsor chancellor
NOMINATED_CHANCELLOR_ID = None
# for remembering the president after a special election cycle, None if not a special election cycle
AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
FAILED_ELECTION_TRACKER = 0  # for tracking failed elections
BOARD = Board(5)  # the game board

# state specific variables

VOTE_PASSED = False  # only valid in election_results state, says whether the vote passed
DRAWN_CARDS = []  # only valid in president_discard and chancellor discard states,
# cards that are up for discarding
CAN_VETO_THIS_ROUND = True  # only valid in chancellor discard state
CURRENT_ACTION = None  # only valid in the action state
CURRENT_INVESTIGATED_PLAYER = None  # only valid in the action state
WINNER = None  # only valid in end state; who the winner of the game is


def start():
    '''
    Main loop which processes the event queue and calls the appropriate function
    based on game state and the dictionary of available functions
    '''
    while True:
        payload = YC.receive()
        print("GAME STATE OUTSIDE: ", GAME_STATE)
        print(payload)

        if GAME_STATE in STATE_HANDLERS:
            handler = STATE_HANDLERS.get(GAME_STATE)
            handler.handle(payload)
        else:
            print(f"Invalid State: {GAME_STATE}")

        print(diagnostics())


# ===================================
# game functions
# ===================================

@SHEPHERD_HANDLER.SETUP.on(SHEPHERD_HEADERS.PLAYER_JOINED)
def player_joined(id: str, name: str, secret: str):
    global PLAYERS

    all_names = [p.name for p in PLAYERS.values()] + \
                [p.name for p in SPECTATORS.values()]

    if id in PLAYERS:
        if PLAYERS[id].name != name or PLAYERS[id].secret != secret:
            YC.send(UI_HEADERS.BAD_LOGIN(
                message="Your login info was bad try again",
                recipients=[id]
            ))
            return
    elif id in SPECTATORS:
        if SPECTATORS[id].name != name or SPECTATORS[id].secret != secret:
            YC.send(UI_HEADERS.BAD_LOGIN(
                message="Your login info was bad try again",
                recipients=[id]
            ))
            return
    elif name in all_names:
        YC.send(UI_HEADERS.BAD_LOGIN(
            message="Somebody already took that name! Try again with a different name",
            recipients=[id]
        ))
        return
    else:
        if len(PLAYERS) >= 10 or GAME_STATE != STATE.SETUP:  # TODO: remove hardcoding
            SPECTATORS[id] = Player(id, name, secret)
            SPECTATORS[id].role = ROLES.SPECTATOR
        else:
            PLAYERS[id] = Player(id, name, secret)

    YC.send(UI_HEADERS.ON_JOIN(
        usernames=[p.name for p in PLAYERS.values()],
        ids=[p.id for p in PLAYERS.values()],
        ongoing_game=GAME_STATE != STATE.SETUP,
    ))

    if GAME_STATE != STATE.SETUP:
        # BEGIN QUESTION 2
        # Whenever a player loads a page during the game, Shepherd will send
        # these headers so that the page can get the information it needs to
        # show the current state of the game. There's no code to fill in here,
        # but you'll be implementing send_policies_enacted so that this can work
        send_individual_setup(id)
        send_current_government(id)
        send_policies_enacted(id)
        send_failed_elections(id)
        # END QUESTION 2

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
        see_roles = role == ROLES.FASCIST or (
            role == ROLES.HITLER and len(PLAYERS) <= 6)
    player_roles = [[oth.name, oth.id, oth.role if see_roles or oth == p else ROLES.NONE]
                    for oth in PLAYERS.values()]
    YC.send(UI_HEADERS.INDIVIDUAL_SETUP(
        roles=player_roles,
        individual_role=role,
        powers=BOARD.board,
        recipients=[id]
    ))


@SHEPHERD_HANDLER.END.on(SHEPHERD_HEADERS.NEXT_STAGE)
def to_setup():
    """
    A function that resets everything and moves the game into setup phase.
    """
    global PLAYERS
    PLAYERS = {}
    global SPECTATORS
    SPECTATORS = {}
    global CARD_DECK
    CARD_DECK = []
    global DISCARD_DECK
    DISCARD_DECK = []
    global PRESIDENT_ID
    PRESIDENT_ID = None
    global PREVIOUS_PRESIDENT_ID
    PREVIOUS_PRESIDENT_ID = None
    global PREVIOUS_CHANCELLOR_ID
    PREVIOUS_CHANCELLOR_ID = None
    global NOMINATED_CHANCELLOR_ID
    NOMINATED_CHANCELLOR_ID = None
    global AFTER_SPECIAL_ELECTION_PRESIDENT_ID
    AFTER_SPECIAL_ELECTION_PRESIDENT_ID = None
    global FAILED_ELECTION_TRACKER
    FAILED_ELECTION_TRACKER = 0
    global GAME_STATE
    GAME_STATE = STATE.SETUP
    YC.send(UI_HEADERS.NEW_LOBBY())


@SHEPHERD_HANDLER.SETUP.on(SHEPHERD_HEADERS.NEXT_STAGE)
def start_game():
    """
    A function that initializes variables that require the number of players.
    """
    global PLAYERS, BOARD, PRESIDENT_ID, CARD_DECK
    if len(PLAYERS) < 5:
        YC.send(UI_HEADERS.NOT_ENOUGH_PLAYERS(players=len(PLAYERS)))
        return

    PRESIDENT_ID = next_president_id()
    CARD_DECK = new_deck()

    # BEGIN QUESTION 1: initialize the list deck with 1 hitler and the relevant number of fascist and liberal cards. Hint: don't use raw strings to represent the roles. Instead, look for a useful class in Utils.py.
    # see the table on page 2 of the rules: https://secrethitler.com/assets/Secret_Hitler_Rules.pdf#page=2. For a challenge, try coming up with a formula for it.

    # TODO: add lines here!

    shuffle_deck(______)

    # Assign roles for each player using the deck.
    player_objs = list(PLAYERS.values())
    for i in range(len(PLAYERS)):
        player_objs[i].role = ________
    # Initialize the board.
    BOARD = ____________
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
    # BEGIN QUESTION 3
    # this is a state-transition function; when this gets called, the state of
    # the game will transition to pick_chancellor, where the president need to
    # choose a chancellor nominee. There's no code to fill out here, but note
    # that this is where the send_chancellor_request gets called.
    GAME_STATE = STATE.PICK_CHANCELLOR
    NOMINATED_CHANCELLOR_ID = None
    send_current_government()  # so UIs know that there is no current chancellor
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
    # BEGIN QUESTION 3
    # This should get called from the send_chancellor_request function. Fill in
    # this function so it returns a list of eligable nominees, as described by
    # the docstring
    # Hint: the function remove_if_exists might be useful

    # TODO: replace the pass with your own code!
    pass

    # END QUESTION 3


@SHEPHERD_HANDLER.PICK_CHANCELLOR.on(SHEPHERD_HEADERS.CHANCELLOR_NOMINATION)
def receive_chancellor_nomination(secret, nominee):
    """
    A function that reads who the president has nominated for chancellor and
    starts the voting process.
    """
    global GAME_STATE, NOMINATED_CHANCELLOR_ID

    if bad_credentials(PRESIDENT_ID, secret):
        return

    GAME_STATE = STATE.VOTE
    NOMINATED_CHANCELLOR_ID = nominee
    send_current_government()
    send_await_vote()


@SHEPHERD_HANDLER.VOTE.on(SHEPHERD_HEADERS.PLAYER_VOTED)
def receive_vote(secret, id, vote):
    """
    A function that notes a vote and acts if the voting is done.
    """
    if bad_credentials(id, secret):
        return
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


@SHEPHERD_HANDLER.ELECTION_RESULTS.on(SHEPHERD_HEADERS.END_ELECTION_RESULTS)
def end_election_results(secret):
    """
    clears everyone's votes, then either advances to the next stage based on whether the
    vote has passed. May enact chaos.
    """
    global PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID, GAME_STATE, DRAWN_CARDS

    if bad_credentials(PRESIDENT_ID, secret):
        return

    for player in PLAYERS.values():
        player.clear_vote()

    if VOTE_PASSED:
        PREVIOUS_PRESIDENT_ID = PRESIDENT_ID
        PREVIOUS_CHANCELLOR_ID = NOMINATED_CHANCELLOR_ID
        # BEGIN QUESTION 5: if chancellor is hitler, and at least 3 fascist
        # policies have been enected,
        # game_over is called and the function is terminated

        # feel free to add lines if needed!
        # if _____________________________________:
        #   ___________________
        #   return

        # END QUESTION 5
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


@SHEPHERD_HANDLER.PRESIDENT_DISCARD.on(SHEPHERD_HEADERS.PRESIDENT_DISCARDED)
def president_discarded(secret, cards, discarded):
    """
    A function that takes the cards left and passes them to the chancellor.
    `cards` contains the remaining two cards.
    """
    global DISCARD_DECK, DRAWN_CARDS, GAME_STATE, CAN_VETO_THIS_ROUND

    # this is to make sure that the person discarding is actually
    # the president and not some hackermans
    if bad_credentials(PRESIDENT_ID, secret):
        return
    GAME_STATE = STATE.CHANCELLOR_DISCARD
    # BEGIN QUESTION 4
    # In order to forward the game after the president discards a card,
    # a few variables need to be updated:
    # - the discarded card needs to be added to DISCARD_DECK
    # - DRAWN_CARDS needs to be set the the remaining two cards
    # - CAN_VETO_THIS_ROUND needs to be set based on a BOARD variable
    ____________________________
    ____________________________
    ____________________________
    # END QUESTION 4
    send_chancellor_discard()


@SHEPHERD_HANDLER.CHANCELLOR_DISCARD.on(SHEPHERD_HEADERS.CHANCELLOR_VETOED)
def chancellor_vetoed(secret):
    """
    A function that asks for the president's response after a chancellor veto.
    """
    global GAME_STATE

    if bad_credentials(NOMINATED_CHANCELLOR_ID, secret):
        return

    GAME_STATE = STATE.CHANCELLOR_VETOED
    send_ask_president_veto()


@SHEPHERD_HANDLER.CHANCELLOR_VETOED.on(SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER)
def president_veto_answer(secret: str, veto: bool):
    """
    A function that receives if the president vetoes or not.
    """
    global FAILED_ELECTION_TRACKER, GAME_STATE, CAN_VETO_THIS_ROUND

    if bad_credentials(PRESIDENT_ID, secret):
        return

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


@SHEPHERD_HANDLER.CHANCELLOR_DISCARD.on(SHEPHERD_HEADERS.CHANCELLOR_DISCARDED)
def chancellor_discarded(secret, card, discarded):
    """
    A function that enacts the policy left over after two have been discarded.
    """
    global GAME_STATE, BOARD, PRESIDENT_ID, CURRENT_ACTION, \
        CURRENT_INVESTIGATED_PLAYER, FAILED_ELECTION_TRACKER

    if bad_credentials(NOMINATED_CHANCELLOR_ID, secret):
        return

    DISCARD_DECK.append(discarded)
    BOARD.enact_policy(card)
    FAILED_ELECTION_TRACKER = 0  # government has successfully enacted a policy
    DISCARD_DECK.append(card)
    send_failed_elections()
    send_policies_enacted()

    # BEGIN QUESTION 5
    # If the fascists enact 6 or more policies, they win.
    # If the liberals enact 5 or more policies, they win.
    # if _______________________:
    #    _______________________
    #    return
    # if _______________________:
    #    _______________________
    #    return
    # END QUESTION 5
    if card == CARDS.LIBERAL or len(BOARD.current_power_list()) == 0:
        advance_president()
        to_pick_chancellor()
    else:
        GAME_STATE = STATE.ACTION
        CURRENT_INVESTIGATED_PLAYER = None
        # note: in any given election cycle, there may be:
        #  - no actions
        #  - a regular action
        #  - a veto enabled and a regular action
        for action in BOARD.current_power_list():
            if action == POWERS.VETO:
                veto()
            else:
                CURRENT_ACTION = action
                send_current_action()


def send_current_action(id=None):
    # BEGIN QUESTION 6
    # This function is called at the beginning of the action stage, as well as
    # when a player reloads the page during the action stage. Here, it calls
    # one of the more specific sender functions depending on which action/power
    # is active. There's no code to fill out here, but make sure you understand
    # how actions work in general.
    send_functions = {
        POWERS.INVESTIGATE_LOYALTY: send_loyalty,
        POWERS.SPECIAL_ELECTION: call_special_election,
        POWERS.POLICY_PEEK: policy_peek,
        POWERS.EXECUTION: execution
    }
    send_functions[CURRENT_ACTION](id)
    # END QUESTION 6


def send_loyalty(id=None):
    """
    A function that begins the Investigate Loyalty power. No player may be
    investigated twice in a game. Also resends headers if Investigate Loyalty
    is ongoing.
    """
    # BEGIN QUESTION 6
    # This sender function handles two seperate cases:
    # - if the president has not chosen a player to investigate yet, send a
    #   BEGIN_INVESTIGATION header with everyone who's eligible to be investigated
    # - if the president has chosen a player to investigate, follow the logic
    #   of a "secure" sender function.
    #    - to the president, send the current investigated player and thier role.
    #      However, if the player is hitler, send ROLES.FASCIST instead.
    #    - to everyone else, send the current investigated player with the role
    #      ROLES.NONE
    if CURRENT_INVESTIGATED_PLAYER is None:
        # TODO: replace the pass with your own code!
        pass

    else:
        # TODO: replace the pass with your own code!
        pass

    # END QUESTION 6


@SHEPHERD_HANDLER.ACTION.on(SHEPHERD_HEADERS.INVESTIGATE_PLAYER)
def investigate_player(secret, player):
    """
    A function that returns the loyalty (as a role) of the player the president
    has asked to investigate using the RECEIVE_INVESTIGATION header. Hitler
    is treated as a fascist.
    """
    # BEGIN QUESTION 6
    # this function gets called halfway through the investigate player action,
    # immediately after the president chooses a player to investigate.
    # set an instance variable of the player so that the player can't be
    # investigated again, and set the global variable that saves which player
    # got investigated.
    # CHALLANGE: what calls this function?
    global CURRENT_INVESTIGATED_PLAYER
    if bad_id(player):
        return
    if bad_credentials(PRESIDENT_ID, secret):
        return
    _________________________
    _________________________
    send_loyalty()
    # END QUESTION 6


def call_special_election(id=None):
    """
    A function that begins the special election power.
    Send the appropriate header to the server with the correct data.
    Anyone except the current president is eligible to be the next president.
    """
    # BEGIN QUESTION 6
    # this is another sender function - send the correct header,
    # with all of the players who are eligible to become the next president

    # TODO: replace the pass with your own code
    pass

    # END QUESTION 6


@SHEPHERD_HANDLER.ACTION.on(SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK)
def perform_special_election(secret, player):
    """
    A function that starts the next session with the new president.
    """
    global PRESIDENT_ID, AFTER_SPECIAL_ELECTION_PRESIDENT_ID
    if bad_id(player):
        return
    if bad_credentials(PRESIDENT_ID, secret):
        return
    AFTER_SPECIAL_ELECTION_PRESIDENT_ID = next_president_id()
    PRESIDENT_ID = player
    send_current_government()
    to_pick_chancellor()


def policy_peek(id=None):
    """
    A function that executes the policy peek power.
    """
    # BEGIN QUESTION 6
    # this is another sender function - send the current header with the top
    # 3 cards. HINT: should this be secure?

    # TODO: replace the pass with your own code
    pass

    # END QUESTION 6


@SHEPHERD_HANDLER.ACTION.on(SHEPHERD_HEADERS.END_POLICY_PEEK)
def end_policy_peek(secret: str):
    """
    A function that ends the policy peek.
    """
    if bad_credentials(PRESIDENT_ID, secret):
        return
    advance_president()
    to_pick_chancellor()


@SHEPHERD_HANDLER.ACTION.on(SHEPHERD_HEADERS.END_INVESTIGATE_PLAYER)
def end_investigate_player(secret: str):
    """
    A function that ends the investigate player.
    """
    if bad_credentials(PRESIDENT_ID, secret):
        return
    advance_president()
    to_pick_chancellor()


def execution(id=None):
    """
    A function that begins the execution power.
    """
    eligibles = list(PLAYERS)
    remove_if_exists(eligibles, PRESIDENT_ID)
    YC.send(UI_HEADERS.BEGIN_EXECUTION(
        eligibles=eligibles,
        recipients=None if id is None else [id]
    ))


@SHEPHERD_HANDLER.ACTION.on(SHEPHERD_HEADERS.PERFORM_EXECUTION)
def perform_execution(secret, player: str):
    """
    A function that executes a player.
    secret - the president's secret, used to verify that the president actually 
             requested the execution
    player - the id of the player to be executed 
    """
    global PRESIDENT_ID, NOMINATED_CHANCELLOR_ID, PREVIOUS_PRESIDENT_ID, PREVIOUS_CHANCELLOR_ID
    if bad_id(player):
        return
    if bad_credentials(PRESIDENT_ID, secret):
        return

    # BEGIN QUESTION 5
    # if Hitler is executed, the liberals win
    if _______________________:
        _______________________
        return
    # END QUESTION 5
    player_obj = PLAYERS.pop(player)

    if player == PRESIDENT_ID:
        PRESIDENT_ID = None
    if player == NOMINATED_CHANCELLOR_ID:
        NOMINATED_CHANCELLOR_ID = None
    if player == PREVIOUS_PRESIDENT_ID:
        PREVIOUS_PRESIDENT_ID = None
    if player == PREVIOUS_CHANCELLOR_ID:
        PREVIOUS_CHANCELLOR_ID = None

    SPECTATORS[player] = player_obj
    advance_president()  # also sends current government, in case chancellor dies
    YC.send(UI_HEADERS.PLAYER_EXECUTED(player=player))
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
    # BEGIN QUESTION 5
    # This is a state transition function - it moves the game into the appropriate
    # state (by setting the GAME_STATE to STATE.END), sets any related variables
    # (in this case, just need to set WINNER), and notifies the UIs of the change
    # (we've already made a sender function for this - you just have to figure out
    # which one it is. Hint: it's in the below "sender functions" section)
    # You shouldn't need to add any addition lines.
    global GAME_STATE, WINNER
    _____________________
    _____________________
    _____________________
    # END QUESTION 5


# ===================================
# sender functions
# ===================================

def send_current_government(id=None):
    YC.send(UI_HEADERS.CURRENT_GOVERNMENT(
        president=PRESIDENT_ID,
        chancellor=NOMINATED_CHANCELLOR_ID,
        recipients=None if id is None else [id]
    ))


def send_policies_enacted(id=None):
    # BEGIN QUESTION 2
    # Using the BOARD object, fill in these blanks to send the correct info
    # Hint: look at utils.py for this header,
    # and look at Board.py to see what instance attributes you need
    YC.send(UI_HEADERS.POLICIES_ENACTED(
        _____________________,
        _____________________,
        recipients=None if id is None else [id]
    ))
    # END QUESTION 2


def send_failed_elections(id=None):
    YC.send(UI_HEADERS.FAILED_ELECTIONS(
        num=FAILED_ELECTION_TRACKER,
        recipients=None if id is None else [id]
    ))


def send_chancellor_request(id=None):
    # BEGIN QUESTION 3
    # Fill this function out! Look at other sender functions for best practices
    # and look at utils.py for what header to use
    # Hint: you should use the eligible_chancellor_nominees function

    # TODO: replace pass with your code!
    pass

    # END QUESTION 3


def send_await_vote(id=None):
    YC.send(UI_HEADERS.AWAIT_VOTE(
        has_voted=players_who_have_voted(),
        recipients=None if id is None else [id]
    ))


def send_election_results(id=None):
    YC.send(UI_HEADERS.ELECTION_RESULTS(
        voted_yes=players_who_have_voted(VOTES.JA),
        voted_no=players_who_have_voted(VOTES.NEIN),
        result=VOTE_PASSED,
        failed_elections=FAILED_ELECTION_TRACKER,
        recipients=None if id is None else [id]
    ))


def send_president_discard(id=None):
    if id is None or id == PRESIDENT_ID:
        YC.send(UI_HEADERS.PRESIDENT_DISCARD(
            cards=DRAWN_CARDS,
            recipients=[PRESIDENT_ID]
        ))
    if id != PRESIDENT_ID:
        YC.send(UI_HEADERS.PRESIDENT_DISCARD(
            cards=[],  # for security, don't want other UIs to know cards
            recipients=[d for d in PLAYERS if d != PRESIDENT_ID]\
                if id is None else [id]
                ))


def send_chancellor_discard(id=None):
    # BEGIN QUESTION 4
    # fill this function out! This is an example of a "secure"
    # sender function - essentially, only the chancellor
    # (NOMINATED_CHANCELLOR_ID) should get to know what the actual cards are,
    # and everyone else should just receive an empty list instead of the cards.
    # Look in utils.py for the correct header, and look at
    # send_president_discard above for an example of how this could work.
    if id is None or id == NOMINATED_CHANCELLOR_ID:
        # TODO: replace pass with your own code!
        pass

    if id != NOMINATED_CHANCELLOR_ID:
        # TODO: replace pass with your own code!
        pass

    # END QUESTION 4


def send_ask_president_veto(id=None):
    YC.send(UI_HEADERS.ASK_PRESIDENT_VETO(
        recipients=None if id is None else [id]
    ))


def send_game_over(id=None):
    YC.send(UI_HEADERS.GAME_OVER(
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
    diag += "\n\tNominated Chancellor: " + \
        str(PLAYERS.get(NOMINATED_CHANCELLOR_ID, None))
    diag += "\n\tPrevious President: " + \
        str(PLAYERS.get(PREVIOUS_PRESIDENT_ID, None))
    diag += "\n\tPrevious Chancellor: " + \
        str(PLAYERS.get(PREVIOUS_CHANCELLOR_ID, None))
    diag += "\n\tElection Tracker: " + str(FAILED_ELECTION_TRACKER)
    diag += "\n\tLiberal Enacted: " + str(BOARD.liberal_enacted)
    diag += "\n\tFascist Enacted: " + str(BOARD.fascist_enacted)
    diag += "\n\tCard Deck: " + str(CARD_DECK)
    return diag


if __name__ == '__main__':
    start()
