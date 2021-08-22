
# Secret Hitler Instructions

Welcome to the Secret Hitler project! We suggest doing the mini-projects before starting the Secret Hitler project - if you haven't done this, head over to MINI-PROJ-1 and MINI-PROJ-2 to get acquainted with some of the tools that you'll be using in this project.

# Question 0: Getting Started

First, let's get the game running. Open the `shepherd-onboarding/shepherd` folder in VSCode (or preferred editor) and then open 3 terminal windows in that folder (in VSCode, you can use the "Split terminal" button):
 - in the first window, run `python3 ydl.py`
 - in the second window, run `python3 server.py`
 - in the third window, run `python3 shepherd.py`

If all goes well, your teminals should have some output similar to this:

![a screenshot of 3 terminals](SHsplitterminal.png)

Open the `index.html` link shown in the second terminal. This should bring you to a login screen - make up any username and password (this won't be saved so it doesn't matter for now) and log in. You should be put into the lobby, where a very wise sheep will tell you fun facts.

Open `index.html` in 4 more tabs, and make up 4 more usernames/passwords. Now that you have 5 players, you should be able to click "start game"! However, when you do so, `shepherd.py` will crash. Your mission in this project is to fix the game, and successfully play a full game of Secret Hitler.

# Question 00: Overview

There are a few main parts to this game:
 - `ydl.py` enables communication between Python files
 - `server.py` is a Flask server that serves the front-end content, much like the Flask server in the first mini-project.
 - `shepherd.py` handles all the game logic. However, it is only partially implemented, so you'll need to write much of it yourself.
 - `index.html` is the logic page.
 - `game.html` is the game page. This is mostly implemented, but you'll be completing it in Question 4.
 - `game.js` is the front-end logic for the game page. However, it is only partially implemented, so you'll need to write much of it yourself.

Most of your time in this project will be spent completing the game logic in `shepherd.py`, so there are a few main data structures you should be aware of:

 - players can be represented by their IDs (strings) or by player objects (which are stored in the `PLAYERS` global variable). Typically, we pass around the IDs, and index the `PLAYERS` dictionary to get the object (i.e. `player_obj = PLAYERS[player_id]`).
 - card decks (such as `CARD_DECK` and `DISCARD_DECK`) are typically lists of strings. The specific strings that represent each card can be found near the bottom of `Utils.py`.
 - powers, votes, and roles are represented by strings, which can be found near the bottom of `Utils.py`.
 - `BOARD` is a `Board` object, which can be made using the constructor in `board.py`.

There are a few more 


# Question 1: Starting a Game

Go to `shepherd.py`, and search for a comment that says "BEGIN QUESTION 1". This is where you'll be implementing part of the logic for `start_game`, in order to set the game up correctly. You'll need to:
    - assign player roles (based on number of players)
    - initialize the board (based on number of players)

Once you have code that you think will work, test it by

# Question 2: __a__
Go to `shepherd.py` and search for a comment that says "BEGIN QUESTION 2". There are two of them. 
- The first one is inside `player_joined`, which is called when a new user logs in. Read the selected section, and feel free to poke inside the functions such as `send_current_government`, which is similar to the one you will be implementing.
- The second is in `send_policies_enacted`, which is called to send the UI information about how many liberal and fascist policies have been enacted. Per the comment description, look for `POLICIES_ENACTED` in utils.py.

# Question 3: __a__
# Question 4: __a__
# Question 5: __a__
# Question 6: __a__


- Game parts to implement
  - Shepherd.py
    1. start_game
       - deck creation/shuffle
       - role assignment
       - board initialization
    2. player_joined_ongoing_game
       - send policies enacted
    3. to_chancellor
       - determine who is eligible to be selected for chancellor
       - send chancellor request header
    4. receive_vote
       - for this function to be called, you must first implement #1 in server.py
       - end game if Hitler is elected chancellor with 3+ fascist policies
    5. president_discarded
       - for this function to be called, you must first implement #1 in server.py
       - all of the function
    6. investigate_player
       - all of the function
  - Utils.py
  - server.py
    1. player_voted
    2. president_discarded
  - game.html
    - socket.on chancellor_request
    - chancellorVoteYes and chancellorVoteNo
      - socket emit
    - display_player_buttons
      - body of forEach
  - Final challenge: all special election business
- Make flowchart of function calls in game flow
- Tests for game parts?
