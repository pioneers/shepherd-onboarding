from utils import VOTES, ROLES


class Player:
    """This is the player class, which is used to track the player's role, the
    players session ID, and the player's vote
    name - String that is the username
    role - Enum of FASCIST, LIBERAL, or HITLER
    id - String used to match an incoming request to the correct player
    vote - Enum of JA, NEIN, or UNDEFINED
    """

    NONE = -1

    def __init__(self, id, name):
        self.id: str = id
        self.name: str = name
        self.vote = VOTES.UNDEFINED
        self.role = ROLES.NONE
        self.investigated: bool = False  # have they been investigated yet?

    def clear_vote(self):
        self.vote = VOTES.UNDEFINED
    
    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return "Name: " + self.name + ", ID: " + str(self.id)
