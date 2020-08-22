# pylint: disable=invalid-name
class SHEPHERD_HEADERS:
    PLAYER_JOINED = "player_joined"
    """
    Header sent to shepherd whenever a player joins or reconnects to the server
    contains:
        name - a string with the name of the user
        id   - a string with the id of the user, calculated as a hash between
               the username and a password
    """

    NEXT_STAGE = "next_stage"
    """
    Header used to tell shepherd that the current phase is over and to advance.
    This is only useful for moving from END->SETUP and SETUP->CHANCELLOR.
    """

    CHANCELLOR_NOMINATION = "chancellor_nomination"
    """
    Header to tell shepherd who the president has nominated to be chancellor
    contains:
        nominee - the id of the player who was nominated to be chancellor
    """

    PLAYER_VOTED = "player_voted"
    """
    Header to tell shepherd the player's vote on the chancellor
    contains:
        id   - the id of the voter
        vote - true if the vote was yes
    """

    PRESIDENT_DISCARDED = "president_discarded"
    """
    Header to tell shepherd that the president has discarded a policy
    contains:
        cards - the two policies left
        discarded - the card discarded (String value)
    """

    CHANCELLOR_DISCARDED = "chancellor_discarded"
    """
    Header to tell shepherd that the chancellor has discarded a policy
    contains:
        card - the card left (String value)
        discarded - the card discarded (String value)
    """

    CHANCELLOR_VETOED = "chancellor_vetoed"
    """
    Header to tell shepherd that the chancellor decided to exercise the veto
    """

    PRESIDENT_VETO_ANSWER = "president_veto_answer"
    """
    Header to tell shepherd if the president decided to veto
    contains:
        veto  - Boolean if the president vetoes
        cards - the cards the chancellor must choose from if the president doesn't veto
    """

    END_POLICY_PEEK = "end_policy_peek"
    """
    Header sent to shepherd to end the policy peek
    """

    INVESTIGATE_PLAYER = "investigate_player"
    """
    Header to tell shepherd which player to investigate
    contains:
        player - the id of the player to investigate
    """

    END_INVESTIGATE_PLAYER = "end_investigate_player"
    """
    Header to tell shepherd to end the player investigation
    """

    SPECIAL_ELECTION_PICK = "special_election_pick"
    """
    Header to tell shepherd who the president picked in the special election
    contains:
        player - the id of the new president
    """

    PERFORM_EXECUTION = "perform_execution"
    """
    Header to tell shepherd to execute a player
    contains:
        player - the id of the player to execute
    """

# pylint: disable=invalid-name


class SERVER_HEADERS:
    ON_JOIN = "on_join"
    """
    Header sent to the server either because a player has reconnected and needs
    to be brought up to speed, or because a new player has connected.
    contains:
        usernames    - an ordered list of usernames
        ids          - an ordered list of ids
        recipients   - a list of players by id who should receive this update. A
                       server may choose not to implement this, at the cost of
                       some extra network usage.
        ongoing_game - a boolean value that is True iff a game has been started.
    """

    FORCE_RECONNECT = "force_reconnect"
    """
    Header sent to server to force all clients to send a PLAYER_JOINED header
    back to shepherd
    """

    NOT_ENOUGH_PLAYERS = "not_enough_players"
    """
    Header sent to server to tell clients that there are not enough players
    contains:
        players - number of players currently joined
    """

    INDIVIDUAL_SETUP = "individual_setup"
    """
    Header sent to server to tell each individual client information necessary to render the ui and have the appropriate game state
        recipients - player ids to send this message to (this is a list, but should only have a single entry)
        roles - a list of player names and their associated roles... [[player, id, role],[player, id, role],...]
        individual_role - the role of the player this is given to
    """

    CHANCELLOR_REQUEST = "chancellor_request"
    """
    Header sent to server to start chancellor state for all players and request
    chancellor nomination from current president through a
    CHANCELLOR_NOMINATION header sent back to shepherd
    contains:
        president   - the id of the current president
        eligibles   - the ids of players who can be nominated
    """

    AWAIT_VOTE = "await_vote"
    """
    Header sent to server to request vote from all players on the chancellor
    through a PLAYER_VOTED header sent back to shepherd
    contains:
        president  - the id of the current president
        chancellor - the id of the nominated chancellor
    """

    PRESIDENT_DISCARD = "president_discard"
    """
    Header sent to server to tell the president to discard a policy
    contains:
        president - the id of the president
        cards     - the three cards from which one must be discarded
    """

    CHANCELLOR_DISCARD = "chancellor_discard"
    """
    Header sent to server to tell the chancellor to discard a policy
    contains:
        chancellor - the id of the chancellor
        cards      - the two cards from which one must be discarded
        can_veto   - True if the chancellor is allowed to exercise a veto
    """

    ASK_PRESIDENT_VETO = "ask_president_veto"
    """
    Header sent to server to tell the president if they want to veto
    contains:
        president - the id of the president
    """

    POLICIES_ENACTED = "policies_enacted"
    """
    Header sent to server to update the number of each policy enacted
    contains:
        liberal - the number of liberal policies enacted
        fascist - the number of fascist policies enacted
    """

    BEGIN_INVESTIGATION = "begin_investigation"
    """
    Header sent to server to tell the president to select a person to investigate
    contains:
        president  - the id of the investigator
        eligibles  - the ids of those who have already been investigated
    """

    RECEIVE_INVESTIGATION = "receive_investigation"
    """
    Header sent to server to give the president the result of the investigation
    contains:
        president - the id of the president
        role      - the role of the person who was investigated
    """

    BEGIN_SPECIAL_ELECTION = "begin_special_election"
    """
    Header sent to server to ask the president to pick a new president
    contains:
        president - the id of the current president
        eligibles - the ids of the players that can be elected (anyone except the president)
    """

    PERFORM_POLICY_PEEK = "perform_policy_peek"
    """
    Header sent to server to allow the president to peek at the top 3 policies
    contains:
        president - the id of the president
        cards     - the top 3 (or fewer if the deck is smaller) cards
    """

    BEGIN_EXECUTION = "begin_execution"
    """
    Header sent to server to ask for an execution
    contains:
        president - the id of the president
        eligibles - players who can be executed (anyone but the president)
    """

    PLAYER_EXECUTED = "player_executed"
    """
    Header sent to server to tell a player they are executed
    contains:
        player - the id of the executed player
    """

    VETO_ENABLED = "veto_enabled"
    """
    Header sent to server to say veto is allowed
    """

    GAME_OVER = "game_over"
    """
    Header sent to server to report the end of the game
    contains:
        winner - the role of the winning team
    """

    REPEAT_MESSAGE = "repeat_message"
    """
    Header used to syncronize an re-connecting client that will send the previous header a second time (but only to that recipient)
    """

# pylint: disable=invalid-name


class LCM_UTILS:
    PRIVILEGED_HEADERS = [SERVER_HEADERS.CHANCELLOR_REQUEST, SERVER_HEADERS.AWAIT_VOTE, SERVER_HEADERS.PRESIDENT_DISCARD, SERVER_HEADERS.CHANCELLOR_DISCARD, SERVER_HEADERS.ASK_PRESIDENT_VETO,
                          SERVER_HEADERS.BEGIN_INVESTIGATION, SERVER_HEADERS.RECEIVE_INVESTIGATION, SERVER_HEADERS.BEGIN_SPECIAL_ELECTION, SERVER_HEADERS.PERFORM_POLICY_PEEK, SERVER_HEADERS.BEGIN_EXECUTION, SERVER_HEADERS.GAME_OVER]

# pylint: disable=invalid-name


class STATE:
    SETUP = "setup"
    END = "end"
    PICK_CHANCELLOR = "pick_chancellor"
    VOTE = "vote"
    POLICY = "policy"
    ACTION = "action"

# pylint: disable=invalid-name


class LCM_TARGETS:
    SHEPHERD = "lcm_target_shepherd"
    SERVER = "lcm_target_server"


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
    """
    BEGIN QUESTION 1
    FIVE_SIX = [[], [], [POWERS.POLICY_PEEK], [
        POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    SEVEN_EIGHT = [[], [POWERS.INVESTIGATE_LOYALTY], [POWERS.SPECIAL_ELECTION], [
        POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    NINE_TEN = [[POWERS.INVESTIGATE_LOYALTY], [POWERS.INVESTIGATE_LOYALTY], [
        POWERS.SPECIAL_ELECTION], [POWERS.EXECUTION], [POWERS.EXECUTION, POWERS.VETO], []]
    """
