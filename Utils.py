# pylint: disable=invalid-name
class SHEPHERD_HEADERS():
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

# pylint: disable=invalid-name
class SERVER_HEADERS():
    PLAYERS = "players"
    """
    Header sent to the server either because a player has reconnected and needs
    to be brought up to speed, or because a new player has connected.
    contains:
        usernames  - an ordered list of usernames
        recipients - a list of players by id who should recieve this update. A
                     server may choose not to implement this, at the cost of
                     some extra network usage.
    """

    FORCE_RECONNECT = "force_reconnect"
    """
    Header sent to server to force all clients to send a PLAYER_JOINED header
    back to shepherd
    """

# pylint: disable=invalid-name
class STATE():
    SETUP = "setup"
    END = "end"
    CHANCELLOR = "chancellor"
    VOTE = "vote"
    POLICY = "policy"
    ACTION = "action"

# pylint: disable=invalid-name
class LCM_TARGETS():
    SHEPHERD = "lcm_target_shepherd"
    SERVER = "lcm_target_server"

class VOTES():
    JA = "ja"
    NEIN = "nein"
    UNDEFINED = "undefined"

class ROLES():
    FASCIST = "fascist"
    LIBERAL = "liberal"
    HITLER = "hitler"

class CARDS():
    FASCIST = "fascist_card"
    LIBERAL = "liberal_card"
