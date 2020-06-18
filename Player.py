from Utils import VOTES

class Player:
    """This is the player class, which is used to track the player's role, the
    players session ID, and the player's vote
    name - String that is the username
    role - Enum of FACIST, LIBERAL, or HITLER
    id - String used to match an incoming request to the correct player
    vote - Enum of JA, NEIN, or UNDEFINED
    """

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.vote = VOTES.UNDEFINED

    def set_role(self, role):
        self.role = role

    def clear_vote(self):
        self.vote = VOTES.UNDEFINED
