from Player import Player
from typing import List, Set, Dict, Tuple, Optional
from Utils import *
from LCM import lcm_send, lcm_register
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

    print(diagnostics())

# ===================================
# game functions
# ===================================


def to_setup(args):
    """
    A function that moves the game into setup phase.
    """
    global CARD_DECK, GAME_STATE
    reset()
    CARD_DECK = new_deck()
    GAME_STATE = STATE.SETUP
    # this needs to be the last thing that happens, since due to how this
    # pseudo-LCM actually works, this will do a significant amount of work on
    # the server's side, and may spawn more LCM messages.
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.FORCE_RECONNECT, {})


def player_joined_new_game(args):
    """
    A function that creates a new player instance for a player who has joined,
    or will allow a player to reconnect if they have joined before.
    """
    global PLAYERS
    id = args["id"]
    print("id is of type", type(id), "and is ")
    name = args["name"]
    lcm_data = {}
    if len(PLAYERS) >= 10:
        # this will need to be a spectator
        SPECTATORS.append(Player(id, name))
        return
    if not id in player_ids(PLAYERS):
        # is this someone reconnecting or joining for the first time?
        print("# Shepherd: Welcome", name)
        PLAYERS += [Player(id, name)]
        lcm_data["recipients"] = player_ids(PLAYERS)
    else:
        lcm_data["recipients"] = [id]
        print("# Shepherd: Welcome back", name)
    lcm_data["usernames"] = player_names(PLAYERS)
    lcm_data["ids"] = player_ids(PLAYERS)
    lcm_data["ongoing_game"] = False
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.ON_JOIN, lcm_data)


def player_joined_ongoing_game(args):
    """
    A function that allows players to reconnect to the game.
    """
    global PLAYERS, SPECTATORS
    id = args["id"]
    name = args["name"]
    if id in player_ids(PLAYERS):
        # is this someone reconnecting or joining for the first time?
        print("# Shepherd: Welcome back", name)
        lcm_data = {"usernames": player_names(PLAYERS), "ids": player_ids(PLAYERS), "recipients": [id], "ongoing_game": True}
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.ON_JOIN, lcm_data)

        # individual setup
        player_roles = []
        player = player_for_id(id)
        lcm_data = {"recipients": [player.id], "individual_role": player.role, "roles": player_roles, "powers": BOARD.board}
        if player.role == ROLES.LIBERAL or (player.role == ROLES.HITLER and len(PLAYERS) > 6):
            for other in PLAYERS:
                if player == other:
                    player_roles.append([player.name, player.id, player.role])
                else:
                    player_roles.append([other.name, other.id , ROLES.NONE])
        elif player.role == ROLES.FASCIST or (player.role == ROLES.HITLER and len(PLAYERS) <= 6):
            for other in PLAYERS:
                player_roles.append([other.name, other.id, other.role])
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.INDIVIDUAL_SETUP, lcm_data)
    else:
        if id not in player_ids(SPECTATORS):
            SPECTATORS.append(Player(id, name))
        print("# Shepherd: Welcome as a spectator", name)
        lcm_data = {"usernames": player_names(PLAYERS), "ids": player_ids(PLAYERS), "recipients": [id], "ongoing_game": True}
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.ON_JOIN, lcm_data)

        # individual setup
        player_roles = []
        spectator = spectator_for_id(id)
        spectator.role = ROLES.SPECTATOR
        lcm_data = {"recipients": [spectator.id], "individual_role": spectator.role, "roles": player_roles, "powers": BOARD.board}
        for other in PLAYERS:
            player_roles.append([other.name, other.id, other.role])
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.INDIVIDUAL_SETUP, lcm_data)

    # policies enacted
    lcm_data = {"liberal": BOARD.liberal_enacted,
                "fascist": BOARD.fascist_enacted,
                "recipients": [id]}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.POLICIES_ENACTED, lcm_data)

    # veto enabled
    if BOARD.can_veto:
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.VETO_ENABLED, {})

    # repeat last server message
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.REPEAT_MESSAGE, {'recipients' : [id]})

def start_game(args):
    """
    A function that initializes variables that require the number of players.
    """
    global PLAYERS, BOARD
    if len(PLAYERS) < 5:
        lcm_data = {"players": len(PLAYERS)}
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.NOT_ENOUGH_PLAYERS, lcm_data)
        return
    deck = [ROLES.LIBERAL] * (len(PLAYERS) // 2 + 1)
    deck += [ROLES.FASCIST] * ((len(PLAYERS) - 1) // 2 - 1)
    deck += [ROLES.HITLER]
    shuffle_deck(deck)
    for i in range(len(PLAYERS)):
        PLAYERS[i].role = deck[i]
    BOARD = Board(len(PLAYERS))
    for player in PLAYERS:
        player_roles = []
        lcm_data = {"recipients": [player.id], "individual_role": player.role, "roles": player_roles, "powers": BOARD.board}
        if player.role == ROLES.LIBERAL or (player.role == ROLES.HITLER and len(PLAYERS) > 6):
            for other in PLAYERS:
                if player == other:
                    player_roles.append([player.name, player.id, player.role])
                else:
                    player_roles.append([other.name, other.id , ROLES.NONE])
        elif player.role == ROLES.FASCIST or (player.role == ROLES.HITLER and len(PLAYERS) <= 6):
            for other in PLAYERS:
                player_roles.append([other.name, other.id, other.role])
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.INDIVIDUAL_SETUP, lcm_data)
    to_chancellor()


def to_chancellor():
    """
    A function that moves the game into the chancellor phase.
    """
    global GAME_STATE
    GAME_STATE = STATE.PICK_CHANCELLOR
    if len(PLAYERS) > 5:
        ineligibles = {player_id(PRESIDENT_INDEX), player_id(
            PREVIOUS_PRESIDENT_INDEX), player_id(PREVIOUS_CHANCELLOR_INDEX)}
    else:
        ineligibles = {player_id(PRESIDENT_INDEX), player_id(PREVIOUS_CHANCELLOR_INDEX)}
    eligibles = [d for d in player_ids(PLAYERS) if d not in ineligibles]
    lcm_data = {"president": player_id(
        PRESIDENT_INDEX), "eligibles": eligibles}
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
    lcm_data = {"president": player_id(
        PRESIDENT_INDEX), "chancellor": chancellor}
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
                game_over(ROLES.FASCIST)
                return
            if len(CARD_DECK) < 3:
                reshuffle_deck()
            GAME_STATE = STATE.POLICY
            lcm_data = {"president": player_id(PRESIDENT_INDEX), "cards": draw_cards(3)}
            lcm_send(LCM_TARGETS.SERVER,
                     SERVER_HEADERS.PRESIDENT_DISCARD, lcm_data)
        else:
            ELECTION_TRACKER += 1
            if chaos():
                ELECTION_TRACKER = 0
                if len(CARD_DECK) < 3:
                    reshuffle_deck()
                card = draw_cards(1)[0]
                BOARD.enact_policy(card)
                PREVIOUS_PRESIDENT_INDEX = Player.NONE
                PREVIOUS_CHANCELLOR_INDEX = Player.NONE
                lcm_data = {"liberal": BOARD.liberal_enacted,
                            "fascist": BOARD.fascist_enacted}
                lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.POLICIES_ENACTED, lcm_data)
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
    lcm_data = {"chancellor": player_id(NOMINATED_CHANCELLOR_INDEX), "cards": cards, "can_veto": BOARD.can_veto}
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
    global ELECTION_TRACKER, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX, CARD_DECK
    value = args["veto"]
    cards = args["cards"]
    if value:
        ELECTION_TRACKER += 1
        if chaos():
            ELECTION_TRACKER = 0
            if len(CARD_DECK) < 3:
                reshuffle_deck()
            card = draw_cards(1)[0]
            BOARD.enact_policy(card)
            PREVIOUS_PRESIDENT_INDEX = Player.NONE
            PREVIOUS_CHANCELLOR_INDEX = Player.NONE
            lcm_data = {"liberal": BOARD.liberal_enacted,
                        "fascist": BOARD.fascist_enacted}
            lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.POLICIES_ENACTED, lcm_data)
        PRESIDENT_INDEX = next_president_index()
        to_chancellor()
    else:
        lcm_data = {"chancellor": player_id(NOMINATED_CHANCELLOR_INDEX), "cards": cards, "can_veto": BOARD.can_veto}
        lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.CHANCELLOR_DISCARD, lcm_data)


def chancellor_discarded(args):
    """
    A function that enacts the policy left over after two have been discarded.
    """
    global GAME_STATE, BOARD, PRESIDENT_INDEX
    card = args["card"]
    discarded = args["discarded"]
    DISCARD_DECK.append(discarded)
    BOARD.enact_policy(card)
    DISCARD_DECK.append(card)
    lcm_data = {"liberal": BOARD.liberal_enacted,
                "fascist": BOARD.fascist_enacted}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.POLICIES_ENACTED, lcm_data)
    if BOARD.fascist_enacted >= 6:
        game_over(ROLES.FASCIST)
        return
    elif card == CARDS.LIBERAL or len(BOARD.current_power_list()) == 0:
        PRESIDENT_INDEX = next_president_index()
        to_chancellor()
    else:
        GAME_STATE = STATE.ACTION
        for action in BOARD.current_power_list():
            if action == POWERS.INVESTIGATE_LOYALTY:
                investigate_loyalty()
            elif action == POWERS.SPECIAL_ELECTION:
                call_special_election()
            elif action == POWERS.POLICY_PEEK:
                policy_peek()
                PRESIDENT_INDEX = next_president_index()
            elif action == POWERS.EXECUTION:
                execution()
            elif action == POWERS.VETO:
                veto()
                PRESIDENT_INDEX = next_president_index()


def investigate_loyalty():
    """
    A function that begins the Investigate Loyalty power.
    """
    investigated = [player_id(i) for i in range(
        len(PLAYERS)) if not PLAYERS[i].investigated]
    lcm_data = {"president": player_id(
        PRESIDENT_INDEX), "eligibles": investigated}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.BEGIN_INVESTIGATION, lcm_data)


def investigate_player(args):
    """
    A function that returns the loyalty (as a role) of the player the president
    has asked to investigate.
    """
    player = player_for_id(args["player"])
    player.investigated = True
    loyalty = ROLES.LIBERAL if player.role == ROLES.LIBERAL else ROLES.FASCIST
    lcm_data = {"president": player_id(PRESIDENT_INDEX), "loyalty": loyalty}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.RECEIVE_INVESTIGATION, lcm_data)


def call_special_election():
    """
    A function that begins the special election power.
    """
    president = player_id(PRESIDENT_INDEX)
    lcm_data = {"president": president, "eligibles": [i for i in player_ids(PLAYERS) if i != president]}
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


def end_policy_peek(args):
    """
    A function that ends the policy peek.
    """
    to_chancellor()

def end_investigate_player(args):
    """
    A function that ends the investigate player.
    """
    global PRESIDENT_INDEX
    PRESIDENT_INDEX = next_president_index()
    to_chancellor()

def execution():
    """
    A function that begins the execution power.
    """
    president = player_id(PRESIDENT_INDEX)
    lcm_data = {"president": president, "eligibles": [i for i in player_ids(PLAYERS) if i != president]}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.BEGIN_EXECUTION, lcm_data)


def perform_execution(args):
    """
    A function that executes a player.
    """
    global PRESIDENT_INDEX, NOMINATED_CHANCELLOR_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX
    p_id = args["player"]
    player = player_for_id(p_id)
    if player.role == ROLES.HITLER:
        game_over(ROLES.LIBERAL)
        return
    ind = player_ids(PLAYERS).index(p_id)
    del PLAYERS[ind]

    PRESIDENT_INDEX = Player.NONE if ind == PRESIDENT_INDEX else (
        PRESIDENT_INDEX - 1 if ind < PRESIDENT_INDEX else PRESIDENT_INDEX)
    NOMINATED_CHANCELLOR_INDEX = Player.NONE if ind == NOMINATED_CHANCELLOR_INDEX else (
        NOMINATED_CHANCELLOR_INDEX - 1 if ind < NOMINATED_CHANCELLOR_INDEX else NOMINATED_CHANCELLOR_INDEX)
    PREVIOUS_PRESIDENT_INDEX = Player.NONE if ind == PREVIOUS_PRESIDENT_INDEX else (
        PREVIOUS_PRESIDENT_INDEX - 1 if ind < PREVIOUS_PRESIDENT_INDEX else PREVIOUS_PRESIDENT_INDEX)
    PREVIOUS_CHANCELLOR_INDEX = Player.NONE if ind == PREVIOUS_CHANCELLOR_INDEX else (
        PREVIOUS_CHANCELLOR_INDEX - 1 if ind < PREVIOUS_CHANCELLOR_INDEX else PREVIOUS_CHANCELLOR_INDEX)

    SPECTATORS.append(player)
    PRESIDENT_INDEX = next_president_index()
    lcm_data = { 'player': p_id }
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.PLAYER_EXECUTED, lcm_data)
    to_chancellor()


def veto():
    """
    A function that turns on the veto power.
    """
    global BOARD
    BOARD.can_veto = True
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.VETO_ENABLED, {})


def game_over(winner):
    """
    A function that reports the end of a game.
    """
    global GAME_STATE
    GAME_STATE = STATE.END
    lcm_data = {"winner": winner}
    lcm_send(LCM_TARGETS.SERVER, SERVER_HEADERS.GAME_OVER, lcm_data)

# ===================================
# helper functions
# ===================================


def player_names(players):
    """
    Returns the list of player names
    """
    return [player.name for player in players]


def player_ids(players):
    """
    Returns the list of player IDs
    """
    return [player.id for player in players]


def player_id(index):
    """
    Returns the ID of a player at an index, returns None if the index is Player.NONE
    """
    if index == Player.NONE:
        return None
    return player_ids(PLAYERS)[index]


def player_for_id(p_id):
    """
    Returns the player with a specified ID
    """
    return PLAYERS[player_ids(PLAYERS).index(p_id)]

def spectator_for_id(s_id):
    """
    Returns the player with a specified ID
    """
    return SPECTATORS[player_ids(SPECTATORS).index(s_id)]


def reset():
    """
    Returns the game state to what it was at the beginning of executions
    """
    global PLAYERS, SPECTATORS, DISCARD_DECK, CARD_DECK, PRESIDENT_INDEX, PREVIOUS_PRESIDENT_INDEX, PREVIOUS_CHANCELLOR_INDEX, NOMINATED_CHANCELLOR_INDEX, AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX, ELECTION_TRACKER
    PLAYERS = []
    SPECTATORS = []
    CARD_DECK = []
    DISCARD_DECK = []
    PRESIDENT_INDEX = 0
    PREVIOUS_PRESIDENT_INDEX = Player.NONE
    PREVIOUS_CHANCELLOR_INDEX = Player.NONE
    NOMINATED_CHANCELLOR_INDEX = Player.NONE
    AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = Player.NONE
    ELECTION_TRACKER = 0


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


def next_president_index():
    """
    Gets the index of the next president, taking into account special elections
    """
    global AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX
    if AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX != Player.NONE:
        value = AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX
        AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = Player.NONE
        return value
    return (PRESIDENT_INDEX + 1) % len(PLAYERS)


def number_of_votes():
    """
    Returns the number of players that recorded votes
    """
    votes = 0
    for player in PLAYERS:
        if player.vote != VOTES.UNDEFINED:
            votes += 1
    return votes


def passing_vote():
    """
    Returns if the recorded votes would elect the proposed government
    """
    diff = 0
    for player in PLAYERS:
        if player.vote == VOTES.JA:
            diff += 1
        else:
            diff -= 1
    return diff > 0


def chaos():
    """
    Returns if the country should be thrown into chaos
    """
    return ELECTION_TRACKER == 3


def diagnostics():
    """
    Returns information about the current game
    """
    diag = "State: " + GAME_STATE + "\n"
    diag += "Players: " + str([str(p) for p in PLAYERS])
    diag += "\nSpectators: " + str([str(s) for s in SPECTATORS])
    diag += "\nPresident: " + \
        ("None" if PRESIDENT_INDEX == -1 else str(PLAYERS[PRESIDENT_INDEX]))
    diag += "\nNominated Chancellor: " + \
        ("None" if NOMINATED_CHANCELLOR_INDEX == -
         1 else str(PLAYERS[NOMINATED_CHANCELLOR_INDEX]))
    diag += "\nPrevious President: " + \
        ("None" if PREVIOUS_PRESIDENT_INDEX == -
         1 else str(PLAYERS[PREVIOUS_PRESIDENT_INDEX]))
    diag += "\nPrevious Chancellor: " + \
        ("None" if PREVIOUS_CHANCELLOR_INDEX == -
         1 else str(PLAYERS[PREVIOUS_CHANCELLOR_INDEX]))
    diag += "\nElection Tracker: " + str(ELECTION_TRACKER)
    diag += "\nLiberal Enacted: " + str(BOARD.liberal_enacted)
    diag += "\nFascist Enacted: " + str(BOARD.fascist_enacted)
    diag += "\nCard Deck: " + str(CARD_DECK)
    return diag

# ===================================
# game variables
# ===================================


# the current game state (setup, pick chancellor, vote, policy, action, end)
GAME_STATE = STATE.SETUP

PLAYERS = []  # a list of Player objects representing the players in the game
SPECTATORS = []  # a list of Player objects representing the spectators
CARD_DECK = new_deck()  # the cards in the deck (not including discarded cards)
DISCARD_DECK = []  # the discarded cards
# the index of the president — this changes before the government is elected
PRESIDENT_INDEX = 0
# the previous elected president (for remembering who is ineligible)
PREVIOUS_PRESIDENT_INDEX = Player.NONE
# the previous elected chancellor (for remembering who is ineligible)
PREVIOUS_CHANCELLOR_INDEX = Player.NONE
# the player who is nominated for chancellor
NOMINATED_CHANCELLOR_INDEX = Player.NONE
# for remembering the president after a special election cycle, Player.NONE if not a special election cycle
AFTER_SPECIAL_ELECTION_PRESIDENT_INDEX = Player.NONE
ELECTION_TRACKER = 0  # for tracking failed elections
BOARD = Board(5)  # the game board

# ===================================
# header to function map
# ===================================

SETUP_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_new_game,
                   SHEPHERD_HEADERS.NEXT_STAGE: start_game}
CHANCELLOR_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_ongoing_game,
                        SHEPHERD_HEADERS.CHANCELLOR_NOMINATION: receive_chancellor_nomination}
VOTE_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_ongoing_game,
                  SHEPHERD_HEADERS.PLAYER_VOTED: receive_vote}
POLICY_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_ongoing_game,
                    SHEPHERD_HEADERS.PRESIDENT_DISCARDED: president_discarded,
                    SHEPHERD_HEADERS.CHANCELLOR_DISCARDED: chancellor_discarded,
                    SHEPHERD_HEADERS.CHANCELLOR_VETOED: chancellor_vetoed,
                    SHEPHERD_HEADERS.PRESIDENT_VETO_ANSWER: president_veto_answer}
ACTION_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_ongoing_game,
                    SHEPHERD_HEADERS.INVESTIGATE_PLAYER: investigate_player,
                    SHEPHERD_HEADERS.SPECIAL_ELECTION_PICK: perform_special_election,
                    SHEPHERD_HEADERS.PERFORM_EXECUTION: perform_execution,
                    SHEPHERD_HEADERS.END_POLICY_PEEK: end_policy_peek,
                    SHEPHERD_HEADERS.END_INVESTIGATE_PLAYER: end_investigate_player
                    }
END_FUNCTIONS = {SHEPHERD_HEADERS.PLAYER_JOINED: player_joined_ongoing_game,
                 SHEPHERD_HEADERS.NEXT_STAGE: to_setup}
