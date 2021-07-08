# pylint: disable=invalid-name
from typing import List, Union
from header import header

class YDL_TARGETS:
    SHEPHERD = "ydl_target_shepherd"
    UI = "ydl_target_server"


class SHEPHERD_HEADERS:
    @header(YDL_TARGETS.SHEPHERD, "player_joined")
    def PLAYER_JOINED(name: str, id: str):
        """
        Header sent to shepherd whenever a player joins or reconnects to the server
        contains:
            name - a string with the name of the user
            id   - a string with the id of the user, calculated as a hash between
                   the username and a password
        """

    @header(YDL_TARGETS.SHEPHERD, "next_stage")
    def NEXT_STAGE(recipients: List[str] = None):
        """
        Header used to tell shepherd that the current phase is over and to advance.
        This is only useful for moving from END->SETUP and SETUP->CHANCELLOR.
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_nomination")
    def CHANCELLOR_NOMINATION(nominee: str, recipients: List[str] = None):
        """
        Header to tell shepherd who the president has nominated to be chancellor
        contains:
            nominee - the id of the player who was nominated to be chancellor
        """

    @header(YDL_TARGETS.SHEPHERD, "player_voted")
    def PLAYER_VOTED(id: str, vote: str, recipients: List[str] = None):
        """
        Header to tell shepherd the player's vote on the chancellor
        contains:
            id   - the id of the voter
            vote - ja if the vote was yes.
        """

    @header(YDL_TARGETS.SHEPHERD, "president_discarded")
    def PRESIDENT_DISCARDED(cards: List[str], discarded: str, recipients: List[str] = None):
        """
        Header to tell shepherd that the president has discarded a policy
        contains:
            cards - the two policies left
            discarded - the card discarded (String value)
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_discarded")
    def CHANCELLOR_DISCARDED(card: str, discarded: str, recipients: List[str] = None):
        """
        Header to tell shepherd that the chancellor has discarded a policy
        contains:
            card - the card left (String value)
            discarded - the card discarded (String value)
        """

    @header(YDL_TARGETS.SHEPHERD, "chancellor_vetoed")
    def CHANCELLOR_VETOED(recipients: List[str] = None):
        """
        Header to tell shepherd that the chancellor decided to exercise the veto
        """

    @header(YDL_TARGETS.SHEPHERD, "president_veto_answer")
    def PRESIDENT_VETO_ANSWER(veto: bool, cards: List[str], recipients: List[str] = None):
        """
        Header to tell shepherd if the president decided to veto
        contains:
            veto  - Boolean if the president vetoes
            cards - the cards the chancellor must choose from if the president doesn't veto
        """

    @header(YDL_TARGETS.SHEPHERD, "end_policy_peek")
    def END_POLICY_PEEK(recipients: List[str] = None):
        """
        Header sent to shepherd to end the policy peek
        """

    @header(YDL_TARGETS.SHEPHERD, "investigate_player")
    def INVESTIGATE_PLAYER(player: str, recipients: List[str] = None):
        """
        Header to tell shepherd which player to investigate
        contains:
            player - the id of the player to investigate
        """

    @header(YDL_TARGETS.SHEPHERD, "end_investigate_player")
    def END_INVESTIGATE_PLAYER(recipients: List[str] = None):
        """
        Header to tell shepherd to end the player investigation
        """

    @header(YDL_TARGETS.SHEPHERD, "special_election_pick")
    def SPECIAL_ELECTION_PICK(player: str, recipients: List[str] = None):
        """
        Header to tell shepherd who the president picked in the special election
        contains:
            player - the id of the new president
        """

    @header(YDL_TARGETS.SHEPHERD, "perform_execution")
    def PERFORM_EXECUTION(player: str, recipients: List[str] = None):
        """
        Header to te
        @header(YDL_TARGETS.UI, l o execute a) sdef hepher(): player
        c, lrecipients: List[str] = Noneontains:
            player - the id of the player to execute
        """

# pylint: disable=invalid-name


class UI_HEADERS:
    @header(YDL_TARGETS.UI, "on_join")
    def ON_JOIN(usernames: List[str], ids: List[str], ongoing_game: bool, recipients: Union[List[str], None]  = None):
        """
        Header sent to the server either because a player has reconnected and needs
        to be brought up to speed, or because a new player has connected.
        contains:
            usernames    - an ordered list of usernames
            ids          - an ordered list of ids
            ongoing_game - a boolean value that is True iff a game has been started.
        """

    @header(YDL_TARGETS.UI, "force_reconnect")
    def FORCE_RECONNECT(recipients: List[str] = None):
        """
        Header sent to server to force all clients to send a PLAYER_JOINED header
        back to shepherd
        """

    @header(YDL_TARGETS.UI, "not_enough_players")
    def NOT_ENOUGH_PLAYERS(players: int, recipients: List[str] = None):
        """
        Header sent to server to tell clients that there are not enough players
        contains:
            players - number of players currently joined
        """

    @header(YDL_TARGETS.UI, "individual_setup")
    def INDIVIDUAL_SETUP(roles: List[List[str]], individual_role: str, powers: List[str], recipients: List[str] = None):
        """
        Header sent to server to tell each individual client information necessary to render the ui and have the appropriate game state
            roles - a list of player names and their associated roles... [[player, id, role],[player, id, role],...]
            individual_role - the role of the player this is given to
            powers - the list of powers for the current game board (from the BOARDS class)
        """

    @header(YDL_TARGETS.UI, "chancellor_request")
    def CHANCELLOR_REQUEST(president: str, eligibles: List[str], recipients: List[str] = None):
        """
        Header sent to server to start chancellor state for all players and request
        chancellor nomination from current president through a
        CHANCELLOR_NOMINATION header sent back to shepherd
        contains:
            president   - the id of the current president
            eligibles   - the ids of players who can be nominated
        """

    @header(YDL_TARGETS.UI, "await_vote")
    def AWAIT_VOTE(president: str, chancellor: str, has_voted: List[str], recipients: List[str] = None):
        """
        Header sent to server to request vote from all players on the chancellor
        through a PLAYER_VOTED header sent back to shepherd
        contains:
            president  - the id of the current president
            chancellor - the id of the nominated chancellor
            has_voted  - the ids of people who have voted
        """

    @header(YDL_TARGETS.UI, "president_discard")
    def PRESIDENT_DISCARD(president: str, cards: List[str], recipients: List[str] = None):
        """
        Header sent to server to tell the president to discard a policy
        contains:
            president - the id of the president
            cards     - the three cards from which one must be discarded
        """

    @header(YDL_TARGETS.UI, "chancellor_discard")
    def CHANCELLOR_DISCARD(chancellor: str, cards: List[str], can_veto: bool, recipients: List[str] = None):
        """
        Header sent to server to tell the chancellor to discard a policy
        contains:
            chancellor - the id of the chancellor
            cards      - the two cards from which one must be discarded
            can_veto   - True if the chancellor is allowed to exercise a veto
        """

    @header(YDL_TARGETS.UI, "ask_president_veto")
    def ASK_PRESIDENT_VETO(president: str, recipients: List[str] = None):
        """
        Header sent to server to tell the president if they want to veto
        contains:
            president - the id of the president
        """

    @header(YDL_TARGETS.UI, "policies_enacted")
    def POLICIES_ENACTED(liberal: int, fascist: int, recipients: List[str] = None):
        """
        Header sent to server to update the number of each policy enacted
        contains:
            liberal - the number of liberal policies enacted
            fascist - the number of fascist policies enacted
        """

    @header(YDL_TARGETS.UI, "begin_investigation")
    def BEGIN_INVESTIGATION(president: str, eligibles: List[str], recipients: List[str] = None):
        """
        Header sent to server to tell the president to select a person to investigate
        contains:
            president  - the id of the investigator
            eligibles  - the ids of those who have haven't been investigated yet
        """

    @header(YDL_TARGETS.UI, "receive_investigation")
    def RECEIVE_INVESTIGATION(president: str, role: str, recipients: List[str] = None):
        """
        Header sent to server to give the president the result of the investigation
        contains:
            president - the id of the president
            role      - the role of the person who was investigated
        """

    @header(YDL_TARGETS.UI, "begin_special_election")
    def BEGIN_SPECIAL_ELECTION(president: str, eligibles: List[str], recipients: List[str] = None):
        """
        Header sent to server to ask the president to pick a new president
        contains:
            president - the id of the current president
            eligibles - the ids of the players that can be elected (anyone except the president)
        """

    @header(YDL_TARGETS.UI, "perform_policy_peek")
    def PERFORM_POLICY_PEEK(president: str, cards: List[str], recipients: List[str] = None):
        """
        Header sent to server to allow the president to peek at the top 3 policies
        contains:
            president - the id of the president
            cards     - the top 3 (or fewer if the deck is smaller) cards
        """

    @header(YDL_TARGETS.UI, "begin_execution")
    def BEGIN_EXECUTION(president: str, eligibles: List[str], recipients: List[str] = None):
        """
        Header sent to server to ask for an execution
        contains:
            president - the id of the president
            eligibles - players who can be executed (anyone but the president)
        """

    @header(YDL_TARGETS.UI, "player_executed")
    def PLAYER_EXECUTED(player: str, recipients: List[str] = None):
        """
        Header sent to server to tell a player they are executed
        contains:
            player - the id of the executed player
        """

    @header(YDL_TARGETS.UI, "veto_enabled")
    def VETO_ENABLED(recipients: List[str] = None):
        """
        Header sent to server to say veto is allowed
        """

    @header(YDL_TARGETS.UI, "game_over")
    def GAME_OVER(winner: str, recipients: List[str] = None):
        """
        Header sent to server to report the end of the game
        contains:
            winner - the role of the winning team
        """

    @header(YDL_TARGETS.UI, "repeat_message")
    def REPEAT_MESSAGE(recipients: List[str] = None):
        """
        Header used to syncronize an re-connecting client that will send the previous header a second time (but only to that recipient)
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
    POLICY = "policy"
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
