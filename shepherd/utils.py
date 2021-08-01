# pylint: disable=invalid-name
from typing import List, Union
from header import header

class YDL_TARGETS:
    SHEPHERD = "ydl_target_shepherd"
    UI = "ydl_target_server"


class SHEPHERD_HEADERS:
    @header(YDL_TARGETS.SHEPHERD, "player_joined")
    def PLAYER_JOINED(name: str, id: str, secret: str):
        """
        Header sent to shepherd whenever a player joins or reconnects to the server
        contains:
            name   - a string with the name of the user
            id     - a string with the id of the user, calculated as a hash between
                     the username and a password
            secret - a string with the secret of the user, calculated as a hash
                     between the username, password, and secret sauce
        """

    @header(YDL_TARGETS.SHEPHERD, "next_stage")
    def NEXT_STAGE():
        """
        Header used to tell shepherd that the current phase is over and to advance.
        This is only useful for moving from END->SETUP and SETUP->CHANCELLOR.
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_nomination")
    def CHANCELLOR_NOMINATION(secret: str, nominee: str):
        """
        Header to tell shepherd who the president has nominated to be chancellor
        contains:
            secret - the president's secret
            nominee - the id of the player who was nominated to be chancellor
        """

    @header(YDL_TARGETS.SHEPHERD, "player_voted")
    def PLAYER_VOTED(secret: str, id: str, vote: str):
        """
        Header to tell shepherd the player's vote on the chancellor
        contains:
            secret - the player's secret
            id   - the id of the voter
            vote - ja if the vote was yes.
        """

    @header(YDL_TARGETS.SHEPHERD, "end_election_results")
    def END_ELECTION_RESULTS(secret: str):
        """
        Header send from president to forward the game after everyone is done
        viewing the election results
        contains:
            secret - the president's secret
        """

    @header(YDL_TARGETS.SHEPHERD, "president_discarded")
    def PRESIDENT_DISCARDED(secret: str, cards: list, discarded: str):
        """
        Header to tell shepherd that the president has discarded a policy
        contains:
            secret    - the president's secret
            cards     - the two policies left
            discarded - the card discarded
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_discarded")
    def CHANCELLOR_DISCARDED(secret: str, card: str, discarded: str):
        """
        Header to tell shepherd that the chancellor has discarded a policy
        contains:
            secret    - the chancellor's secret
            card      - the card left
            discarded - the card discarded
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_vetoed")
    def CHANCELLOR_VETOED(secret: str):
        """
        Header to tell shepherd that the chancellor decided to exercise the veto
        contains:
            secret - the chancellor's secret
        """

    @header(YDL_TARGETS.SHEPHERD, "president_veto_answer")
    def PRESIDENT_VETO_ANSWER(secret: str, veto: bool):
        """
        Header to tell shepherd if the president decided to veto
        contains:
            secret - the president's secret
            veto   - Boolean if the president vetoes
        """

    @header(YDL_TARGETS.SHEPHERD, "end_policy_peek")
    def END_POLICY_PEEK(secret: str):
        """
        Header sent to shepherd to end the policy peek
        contains:
            secret - the president's secret
        """

    @header(YDL_TARGETS.SHEPHERD, "investigate_player")
    def INVESTIGATE_PLAYER(secret: str, player: str):
        """
        Header to tell shepherd which player to investigate
        contains:
            secret - the president's secret
            player - the id of the player to investigate
        """

    @header(YDL_TARGETS.SHEPHERD, "end_investigate_player")
    def END_INVESTIGATE_PLAYER(secret: str):
        """
        Header to tell shepherd to end the player investigation
        contains:
            secret - the president's secret
        """

    @header(YDL_TARGETS.SHEPHERD, "special_election_pick")
    def SPECIAL_ELECTION_PICK(secret: str, player: str):
        """
        Header to tell shepherd who the president picked in the special election
        contains:
            secret - the president's secret
            player - the id of the new president
        """

    @header(YDL_TARGETS.SHEPHERD, "perform_execution")
    def PERFORM_EXECUTION(secret: str, player: str):
        """
        Header to pick player to execute
        contains:
            secret - the president's secret
            player - the id of the player to execute
        """

# pylint: disable=invalid-name


class UI_HEADERS:
    @header(YDL_TARGETS.UI, "on_join")
    def ON_JOIN(usernames: list, ids: list, ongoing_game: bool, recipients = None):
        """
        Header sent to the server either because a player has reconnected and needs
        to be brought up to speed, or because a new player has connected.
        contains:
            usernames    - an ordered list of usernames
            ids          - an ordered list of ids
            ongoing_game - a boolean value that is True iff a game has been started.
        """

    @header(YDL_TARGETS.UI, "bad_login")
    def BAD_LOGIN(message: str, recipients = None):
        """
        Header sent to server to tell a player that their login attempt was unsuccessful
        """

    @header(YDL_TARGETS.UI, "not_enough_players")
    def NOT_ENOUGH_PLAYERS(players: int, recipients = None):
        """
        Header sent to server to tell clients that there are not enough players
        contains:
            players - number of players currently joined
        """

    @header(YDL_TARGETS.UI, "individual_setup")
    def INDIVIDUAL_SETUP(roles: list, individual_role: str, powers: list, recipients = None):
        """
        Header sent to server to tell each individual client information necessary to render the ui and have the appropriate game state
        contains:
            roles - a list of player names and their associated roles... [[player, id, role],[player, id, role],...]
            individual_role - the role of the player this is given to
            powers - the list of powers for the current game board (from the BOARDS class)
        """

    @header(YDL_TARGETS.UI, "current_government")
    def CURRENT_GOVERNMENT(president: str, chancellor, recipients = None):
        """
        Header sent to the server to inform everyone who the current president and chancellor are
        contains:
            president   - the id of the current president
            chancellor  - the id of the nominated chancellor (or None/null)
        """

    @header(YDL_TARGETS.UI, "chancellor_request")
    def CHANCELLOR_REQUEST(eligibles: list, recipients = None):
        """
        Header sent to server to start chancellor state for all players and request
        chancellor nomination from current president through a
        CHANCELLOR_NOMINATION header sent back to shepherd
        contains:
            eligibles   - the ids of players who can be nominated
        """

    @header(YDL_TARGETS.UI, "await_vote")
    def AWAIT_VOTE(has_voted: list, recipients = None):
        """
        Header sent to server to request vote from all players on the chancellor
        through a PLAYER_VOTED header sent back to shepherd
        contains:
            has_voted  - the ids of people who have voted
        """

    @header(YDL_TARGETS.UI, "election_results")
    def ELECTION_RESULTS(voted_yes: list, voted_no: list, result: bool, failed_elections: int, recipients = None):
        """
        Header sent to server to tell everyone how everyone voted, and 
        display the result of the election. Gives president a button which
        president will use to forward the game
        contains:
            voted_yes - the ids of the players who voted yes
            voted_no  - the ids of the players who voted no
            result    - true if the vote passed, false if the vote did not pass
            failed_elections - the number of failed elections in a row
        """

    @header(YDL_TARGETS.UI, "president_discard")
    def PRESIDENT_DISCARD(cards: list, recipients = None):
        """
        Header sent to server to tell the president to discard a policy
        contains:
            cards     - the three cards from which one must be discarded
        """

    @header(YDL_TARGETS.UI, "chancellor_discard")
    def CHANCELLOR_DISCARD(cards: list, can_veto: bool, recipients = None):
        """
        Header sent to server to tell the chancellor to discard a policy
        contains:
            cards      - the two cards from which one must be discarded
            can_veto   - True if the chancellor is allowed to exercise a veto
        """

    @header(YDL_TARGETS.UI, "ask_president_veto")
    def ASK_PRESIDENT_VETO(recipients = None):
        """
        Header sent to server to ask the president if they want to veto
        """

    @header(YDL_TARGETS.UI, "policies_enacted")
    def POLICIES_ENACTED(liberal: int, fascist: int, can_veto: bool, recipients = None):
        """
        Header sent to server to update the number of each policy enacted
        contains:
            liberal - the number of liberal policies enacted
            fascist - the number of fascist policies enacted
            can_veto - whether the veto power has been enabled
        """

    @header(YDL_TARGETS.UI, "failed_elections")
    def FAILED_ELECTIONS(num: int, recipients = None):
        """
        Header send to server to update the number of failed elections
        contains:
            num - the number of failed elections
        """

    @header(YDL_TARGETS.UI, "begin_investigation")
    def BEGIN_INVESTIGATION(eligibles: list, recipients = None):
        """
        Header sent to server to tell the president to select a person to investigate
        contains:
            eligibles  - the ids of those who have haven't been investigated yet
        """

    @header(YDL_TARGETS.UI, "receive_investigation")
    def RECEIVE_INVESTIGATION(player: str, role: str, recipients = None):
        """
        Header sent to server to give the president the result of the investigation
        contains:
            player    - the id of the person who was investigate
            role      - the role of the person who was investigated
        """

    @header(YDL_TARGETS.UI, "begin_special_election")
    def BEGIN_SPECIAL_ELECTION(eligibles: list, recipients = None):
        """
        Header sent to server to ask the president to pick a new president
        contains:
            eligibles - the ids of the players that can be elected (anyone except the president)
        """

    @header(YDL_TARGETS.UI, "perform_policy_peek")
    def PERFORM_POLICY_PEEK(cards: list, recipients = None):
        """
        Header sent to server to allow the president to peek at the top 3 policies
        contains:
            cards     - the top 3 (or fewer if the deck is smaller) cards
        """

    @header(YDL_TARGETS.UI, "begin_execution")
    def BEGIN_EXECUTION(eligibles: list, recipients = None):
        """
        Header sent to server to ask for an execution
        contains:
            eligibles - players who can be executed (anyone but the president)
        """

    @header(YDL_TARGETS.UI, "player_executed")
    def PLAYER_EXECUTED(player: str, recipients = None):
        """
        Header sent to server to tell everyone who has been executed
        contains:
            player - the id of the executed player
        """

    @header(YDL_TARGETS.UI, "game_over")
    def GAME_OVER(winner: str, roles, recipients = None):
        """
        Header sent to server to report the end of the game
        contains:
            winner - the role of the winning team
            roles - the [id, name, role] of all the players
        """
    
    @header(YDL_TARGETS.UI, "new_lobby")
    def NEW_LOBBY(recipients = None):
        """
        Header sent to server to tell clients that a new lobby has been made
        """


# A dictionary of pages -> whether page is password protected
# password.html should not be included in this list, since
# server.py will just route to that automatically
# add additional pages here

UI_PAGES = {
    "index.html": False,
    "game.html": False
}




class LCM_UTILS:
    PRIVILEGED_HEADERS = [UI_HEADERS.CHANCELLOR_REQUEST, UI_HEADERS.AWAIT_VOTE, UI_HEADERS.PRESIDENT_DISCARD, UI_HEADERS.CHANCELLOR_DISCARD, UI_HEADERS.ASK_PRESIDENT_VETO,
                          UI_HEADERS.BEGIN_INVESTIGATION, UI_HEADERS.RECEIVE_INVESTIGATION, UI_HEADERS.BEGIN_SPECIAL_ELECTION, UI_HEADERS.PERFORM_POLICY_PEEK, UI_HEADERS.BEGIN_EXECUTION, UI_HEADERS.GAME_OVER]
    """
    headers that the server saves
    """
# pylint: disable=invalid-name


class STATE:
    SETUP = "setup"
    END = "end"
    PICK_CHANCELLOR = "pick_chancellor"
    VOTE = "vote"
    ELECTION_RESULTS = "election_results"
    PRESIDENT_DISCARD = "president_discard"
    CHANCELLOR_DISCARD = "chancellor_discard"
    CHANCELLOR_VETOED = "chancellor_veto"
    ACTION = "action"

# pylint: disable=invalid-name


class VOTES:
    JA = "ja"
    NEIN = "nein"
    UNDEFINED = "undefined"


class ROLES:
    FASCIST = "fascist"
    LIBERAL = "liberal"
    HITLER = "hitler"
    SPECTATOR = "spectator"
    NONE = "unknown"


class CARDS:
    FASCIST = "fascist_card"
    LIBERAL = "liberal_card"


class POWERS:
    INVESTIGATE_LOYALTY = "investigate_loyalty"
    SPECIAL_ELECTION = "special_election"
    POLICY_PEEK = "policy_peek"
    EXECUTION = "execution"
    VETO = "veto"


class BOARDS:
    # BEGIN QUESTION 1: each arrangement contains a list of 6 lists. List i contains each power that occurs after the (i + 1)th fascist policy is passed.
    FIVE_SIX = [[], [], [POWERS.POLICY_PEEK], [
        POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    SEVEN_EIGHT = [[], [POWERS.INVESTIGATE_LOYALTY], [POWERS.SPECIAL_ELECTION], [
        POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    NINE_TEN = [[POWERS.INVESTIGATE_LOYALTY], [POWERS.INVESTIGATE_LOYALTY], [
        POWERS.SPECIAL_ELECTION], [POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    # END QUESTION 1
