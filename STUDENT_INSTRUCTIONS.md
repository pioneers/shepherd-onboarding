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
