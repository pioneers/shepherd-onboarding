from Utils import BOARDS, CARDS

class Board:
    """Tracks the current board and the number of policies enacted.
    board           - the board being used
    liberal_enacted - the number of liberal policies enacted
    fascist_enacted - the number of fascist policies enacted
    """

    def __init__(self, num_players):
        if num_players == 5 or num_players == 6:
            self.board = BOARDS.FIVE_SIX
        elif num_players == 7 or num_players == 8:
            self.board = BOARDS.SEVEN_EIGHT
        else:
            self.board = BOARDS.NINE_TEN
        self.liberal_enacted = 0
        self.fascist_enacted = 0

    def enact_policy(self, card):
        """
        Enact the policy denoted by the card.
        """
        if card == CARDS.LIBERAL:
            self.liberal_enacted += 1
        else:
            self.fascist_enacted += 1

    def current_power_list(self):
        """
        Return the policies under the last enacted fascist card.
        """
        if self.fascist_enacted < 1 or self.fascist_enacted > len(self.board):
            return []
        return self.board[self.fascist_enacted - 1]
