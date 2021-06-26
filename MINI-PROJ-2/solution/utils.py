# pylint: disable=invalid-name
from typing import List
from header import header

class YDL_TARGETS:
    PING = "ydl_target_ping"
    PONG = "ydl_target_pong"


class PING_HEADERS:
    @header(YDL_TARGETS.PING, "respond")
    def RESPOND(text: str, time: float):
        """
        Header sent to ping with a response. Includes the time that the response was sent.
        contains:
            name - a string with the name of the user
            id   - a string with the id of the user, calculated as a hash between
                   the username and a password
        """


class PONG_HEADERS:
    @header(YDL_TARGETS.PONG, "notify")
    def NOTIFY(text: str):
        """
        Header sent to pong to notify it of something. Of what? Who knows?
        contains:
            usernames    - an ordered list of usernames
            ids          - an ordered list of ids
            ongoing_game - a boolean value that is True iff a game has been started.
        """
    @header(YDL_TARGETS.PONG, "repeat")
    def REPEAT():
        """
        Header sent to pong to ask it to repeat the last message that it sent.
        If pong did not send any messages, don't send anything back
        """

class RESPONSES():
    CANNED_RESPONSES = {
        "cheese": "I like cheese",
        "shepherd": "baaaaaaa",
        "ydl": "yodelayheehoo",
        "blueberry": "Goats eat blueberries"
    }
    BANNED_RESPONSES = [
        "stanford",
        "tree",
        "is_fork",
        "St. Anford's school for gifted and special children"
    ]




