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
    """

    CHANCELLOR_DISCARDED = "chancellor_discarded"
    """
    Header to tell shepherd that the chancellor has discarded a policy
    contains:
        card - the card left (String value)
    """

# pylint: disable=invalid-name
class SERVER_HEADERS:
    PLAYERS = "players"
    """
    Header sent to the server either because a player has reconnected and needs
    to be brought up to speed, or because a new player has connected.
    contains:
        usernames  - an ordered list of usernames
        recipients - a list of players by id who should receive this update. A
                     server may choose not to implement this, at the cost of
                     some extra network usage.
    """

    FORCE_RECONNECT = "force_reconnect"
    """
    Header sent to server to force all clients to send a PLAYER_JOINED header
    back to shepherd
    """

    CHANCELLOR_REQUEST = "chancellor_request"
    """
    Header sent to server to start chancellor state for all players and request
    chancellor nomination from current president through a
    CHANCELLOR_NOMINATION header sent back to shepherd
    contains:
        president   - the id of the current president
        ineligibles - the ids of players who cannot be nominated
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
        cards - the three cards from which one must be discarded
    """

    CHANCELLOR_DISCARD = "chancellor_discard"
    """
    Header sent to server to tell the chancellor to discard a policy
    contains:
        cards - the two cards from which one must be discarded
    """

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

class CARDS:
    FASCIST = "fascist_card"
    LIBERAL = "liberal_card"
