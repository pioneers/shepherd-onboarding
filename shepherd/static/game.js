      // initialize socket
      console.log("loaded");
      let socket;
      try {
        socket = io();
      } catch (error) {
        document.getElementById(
          "titleText"
        ).textContent = `Looks like you don't have a full connection to the server! Try checking your internet connection!`;
        throw error;
      }

      // global variables
      let cardClickState = 0; // 0: don't click, 1: president discarding, 2: chancellor discarding
      let currentCards = []; // the cards from which the president/chancellor must discard a card
      // the ids of all elements on the screen, used to easily show/hide elements
      let allIDs = [
        "titleText",
        "playersText",
        "startGameButton",
        "miscEntryText",
        "chancellorVoteYesButton",
        "chancellorVoteNoButton",
        "presidentEndElectionResultsButton",
        "card1Button",
        "card2Button",
        "card3Button",
        "endPolicyPeekButton",
        "chancellorVetoButton",
        "presidentVetoButton",
        "presidentNoVetoButton",
        "startNewGameButton",
        "joinNewLobbyButton",
        "signOutButton",
        "endInvestigatePlayerButton",
        "facts",
      ];
      let idToName = {}; // map from player id to name
      let isSpectator = false; // true if this client is a spectator
      let roles = []; // the roles of each player, formatted [name, id, role]
      let liberal_color = "#5681df";
      let fascist_color = "#d76f54";

      let president_id = null;
      let chancellor_id = null;

      // get player information and display waiting room
      const urlParams = new URLSearchParams(window.location.search);
      const name = urlParams.get("name");
      const id = urlParams.get("id");
      const secret = urlParams.get("secret");
      document.getElementById(
        "titleText"
      ).textContent = `BAA play here, you are ${name}`;
      console.log(name);
      if (!id || !name || !secret) {
        location.href = "/index.html"; //redirect to login
      }

      //initialize random fact
      refreshFacts();

      function logg() {
        //as of now, do nothing
        //add logging later?
      }

      function send() {
        socket.emit("ui-to-server", "no password lul", ...arguments);
        let logstr = "";
        try {
          for (let a = 0; a < arguments.length; a++) logstr += arguments[a];
        } catch (err) {
          console.log(err);
          logstr = "[logging error]";
        }
        logg(logstr);
      }

      socket.on("connect", () => {
        socket.emit("join", name, id);
        send(
          "player_joined",
          JSON.stringify({name, id, secret})
        );
      });

      socket.on("bad_login", (data) => {
        const { message } = JSON.parse(data);
        location.href = "index.html?message=" + encodeURIComponent(message);
      });

      // receive information from shepherd

      socket.on("new_lobby", () => {
        hideAllExcept(["miscEntryText"]);
        document.getElementById("joinNewLobbyButton").style.display = "inline-block";
        document.getElementById("signOutButton").style.display = "inline-block";
        document.getElementById("miscEntryText").textContent = "A new game has been made";
        socket.close();
      });

      // add a player to the game
      socket.on("on_join", (data) => {
        const { usernames, ids, ongoing_game: ongoingGame } = JSON.parse(data);

        console.log("Player joined");
        console.groupCollapsed();
        console.log("players are: ", usernames);
        console.log("player ids are: ", ids);
        console.log("ongoing game is ", ongoingGame);
        console.groupEnd();

        // store the player's id and name in a dictionary
        ids.forEach((id, index) => {
          idToName[id] = usernames[index];
        });

        // print the players on the screen
        document.getElementById("playersText").textContent =
          "Players: " + usernames.toString();

        // let the player start the game if possible
        if (!ongoingGame && usernames.length >= 5) {
          show("startGameButton");
        }
      });

      socket.on("current_government", (data) => {
        const {president, chancellor} = JSON.parse(data);
        president_id = president //set global var
        chancellor_id = chancellor //set global var
        set_placards(president_id, chancellor_id);
      });

      // the president must select a chancellor
      socket.on("chancellor_request", (data) => {
        const { eligibles } = JSON.parse(data);

        //in case the last nomination was a failure, or an investigation happened
        clear_highlights();  

        // BEGIN QUESTION 3
        // fill in appropriate messages for the president (who need to select a 
        // nominee), and for everyone else (who is just waiting for the president)
        // Make sure to test your code after filling this out!
        if (president_id === id) {
          // if this player is the president, have them select a chancellor nominee
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "Select your chancellor nominee";
          display_player_buttons(eligibles, "nominateChancellor");
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The president is selecting a chancellor nominee";
        }
        // END QUESTION 3
      });

      // tell the player they need to vote
      socket.on("await_vote", (data) => {
        const { has_voted } = JSON.parse(data);

        const presidentName = idToName[president_id];
        const chancellorName = idToName[chancellor_id];
        show_highlight(chancellor_id);
        set_placards(president_id); // no chancellor placard since just nominee
        let voteText = `${presidentName} has nominated ${chancellorName}. `;
        if (isSpectator) {
          hideAllExcept(["miscEntryText"]);
          voteText += "You are a sad boi who cannot vote.";
        } else if (has_voted.includes(id)) {
          hideAllExcept(["miscEntryText"]);
          voteText += "Waiting for others to vote...";
        } else {
          // if this player is not a spectator, they can vote
          hideAllExcept([
            "miscEntryText",
            "chancellorVoteYesButton",
            "chancellorVoteNoButton",
          ]);
          voteText += "Please vote.";
        }
        document.getElementById("miscEntryText").textContent = voteText;
        show_votes(has_voted);
      });

      socket.on("election_results", (data) => {
        const { voted_yes, voted_no, result, failed_elections } = JSON.parse(data);

        if (result) {
          clear_highlights();
          set_placards(president_id, chancellor_id);
        } else {
          show_highlight(chancellor_id); //will be cleared in chancellor_request
          set_placards(president_id);
        }

        failedElectionMessages = [
          "There have been no failed nominations in recent history.",
          "This is the first failed nomination in recent history.",
          "This is the second failed nomination in recent history.",
          "This is the third failed nomination in recent history. Chaos is upon us."
        ];
        if (president_id === id) {
          hideAllExcept(["presidentEndElectionResultsButton", "miscEntryText"]);
        } else {
          hideAllExcept(["miscEntryText"]);
        }
        document.getElementById("miscEntryText").textContent = result
          ? "The vote has passed!"
          : failedElectionMessages[failed_elections];
        show_failed_elections(failed_elections);
        show_jas_neins(voted_yes, voted_no);
      });

      function endElectionResults() {
        send("end_election_results", JSON.stringify({secret}));
      }

      socket.on("failed_elections", (data) => {
        const { num } = JSON.parse(data);
        show_failed_elections(num);
      })

      // the president must discard a card
      socket.on("president_discard", (data) => {
        const { cards } = JSON.parse(data);

        cardClickState = 1;
        currentCards = cards;

        if (president_id == id) {
          hideAllExcept([
            "miscEntryText",
            "card1Button",
            "card2Button",
            "card3Button",
          ]);
          document.getElementById("miscEntryText").textContent =
            "The vote has passed. Discard a policy.";
          show_cards(cards[0], cards[1], cards[2]);
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The vote has passed. The president is discarding a policy.";
        }
      });

      // the chancellor must discard a card
      socket.on("chancellor_discard", (data) => {
        const { cards, can_veto } = JSON.parse(data);

        cardClickState = 2;
        currentCards = cards;

        if (chancellor_id == id) {
          hideAllExcept(["miscEntryText", "card1Button", "card2Button"]);
          document.getElementById("miscEntryText").textContent =
            "Discard a policy.";
          show_cards(cards[0], cards[1], "fascist_card"); // last card doesn't matter because it's not shown
          // give the chancellor the option to veto if possible
          if (can_veto) {
            show("chancellorVetoButton");
          }
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The chancellor is discarding a policy";
        }
      });

      // inform the player of their role and display the other players
      socket.on("individual_setup", (data) => {
        const { 
          individual_role, 
          roles: all_roles, 
          powers
        } = JSON.parse(data);
        roles = all_roles;

        document.getElementById("startGameButton").style.display = "none";

        if (individual_role == "spectator") {
          isSpectator = true;
        }

        display_players(roles);
        display_powers(powers);
      });

      // after the chancellor has vetoed, ask if the president wants to
      socket.on("ask_president_veto", (data) => {
        if (president_id == id) {
          hideAllExcept([
            "miscEntryText",
            "presidentVetoButton",
            "presidentNoVetoButton",
          ]);
          document.getElementById("miscEntryText").textContent =
            "The chancellor has decided to veto. Do you?";
          document.getElementById("presidentVetoButton").textContent = "Yes";
          document.getElementById("presidentNoVetoButton").textContent = "No";
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The chancellor has decided to veto. Waiting on president response.";
        }
      });

      // end the game and show the start new game button
      socket.on("game_over", (data) => {
        const { winner, roles: all_roles } = JSON.parse(data);
        roles = all_roles;
        display_players(roles);
        set_placards(president_id, chancellor_id);
        hideAllExcept(["miscEntryText", "startNewGameButton"]);
        document.getElementById("miscEntryText").textContent =
          winner + "s win!";
      });

      // hide all elements on the screen except for those in idArray
      function hideAllExcept(idArray) {
        allIDs.forEach((elementID, index) => {
          if (idArray.includes(elementID)) {
            document.getElementById(elementID).style.display = "block";
          } else {
            document.getElementById(elementID).style.display = "none";
          }
        });
      }
      // show a specific element on the screen
      function show(elementID) {
        document.getElementById(elementID).style.display = "block";
      }

      // tell the president to select a player to be the next president
      socket.on("begin_special_election", (data) => {
        const { eligibles } = JSON.parse(data);

        if (president_id == id) {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "Special election. Select a player to be the next president.";
          display_player_buttons(eligibles, "specialElection");
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "Special election. The president is selecting the next president.";
        }
      });

      function show_cards(card1, card2, card3) {
        cards = [card1, card2, card3];
        for (let a in cards) {
          let el = document.getElementById(`card${parseInt(a) + 1}Button`);
          let f = cards[a] == "fascist_card";
          el.textContent = f ? "Fascist" : "Liberal";
          el.style.background = f ? fascist_color : liberal_color;
        }
      }

      // let the president peek at the top policies
      socket.on("perform_policy_peek", (data) => {
        const { cards } = JSON.parse(data);

        cardClickState = 0;

        if (president_id == id) {
          hideAllExcept([
            "miscEntryText",
            "card1Button",
            "card2Button",
            "card3Button",
            "endPolicyPeekButton",
          ]);
          document.getElementById("miscEntryText").textContent =
            "These are the top 3 cards in the pile.";
          show_cards(cards[0], cards[1], cards[2]);
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The president is reading the top 3 cards in the pile.";
        }
      });

      // perform the execution of a player
      socket.on("player_executed", (data) => {
        const { player: executedPlayer } = JSON.parse(data);

        // only keep players who are not the executed player
        roles = roles.filter((player) => player[1] !== executedPlayer);
        delete idToName[executedPlayer];

        // make the executed player a spectator
        if (executedPlayer == id) {
          isSpectator = true;
        }

        // remove the executed player from the display
        allIDs = allIDs.filter(
          (elementID) => elementID !== `selectPlayer${executedPlayer}`
                      && elementID !== `votePlayerID${executedPlayer}`
                      && elementID !== `jaOrNeinID${executedPlayer}`
        );

        // display the remaining players
        display_players(roles);
      });

      // nominate chancellor (called by the president)
      function nominateChancellor(id) {
        console.log(`chancellor is being nominated to ${id}`);
        send(
          "chancellor_nomination",
          JSON.stringify({
            secret,
            nominee: id,
          })
        );
      }

      // tell the president to execute a player
      socket.on("begin_execution", (data) => {
        const { eligibles } = JSON.parse(data);

        if (president_id == id) {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "Select a player to execute.";
          display_player_buttons(eligibles, "performExecution");
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "The president is selecting a player to execute.";
        }
      });

      // update the board based on the number of policies enacted
      socket.on("policies_enacted", (data) => {
        // BEGIN QUESTION 2
        // this is where the policies_enacted header that Shepherd sends gets
        // received on the front-end. This first unpacks the header,
        // then updates the UI element that corresponds to the enacted policies
        // There's no code to fill in here, but feel free to play around with
        // this. Try uncommenting/modifying the console.log statement!
        const { liberal, fascist } = JSON.parse(data);
        // console.log("Received a policies_enacted header from Shepherd!");
        updateCards(liberal, fascist);
        // END QUESTION 2
      });

      // ask the president to select a player to be investigated
      socket.on("begin_investigation", (data) => {
        const { eligibles } = JSON.parse(data);

        if (president_id == id) {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
            "Select who you want to investigate.";
          display_player_buttons(eligibles, "investigatePlayer");
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
          "The president is investigating a player's loyalty.";
        }
      });

      // tell the president the role of the player they investigated
      socket.on("receive_investigation", (data) => {
        const { player, role:loyalty } = JSON.parse(data);

        let player_name = idToName[player];
        show_highlight(player)
        if (president_id === id) {
          hideAllExcept(["miscEntryText", "endInvestigatePlayerButton"]);
          document.getElementById(
            "miscEntryText"
          ).textContent = `${player_name}'s role is ${loyalty}`;
        } else {
          hideAllExcept(["miscEntryText"]);
          document.getElementById("miscEntryText").textContent =
          `The president has investigated ${player_name}.`;
        }
      });

      /*
      This function votes yes by emitting a player_voted event to the server.
      You are responsible for finding the relevant header in Utils.py.
    */
      function chancellorVoteYes() {
        // vote yes on chancellor
        hideAllExcept(["miscEntryText"]); // text will be updated on next await_vote header
        /*
        BEGIN QUESTION 2
      */
        send("player_voted", JSON.stringify({ secret, id, vote: "ja" }));
      }

      /*
      This function votes no by emitting a player_voted event to the server.
      You are responsible for finding the relevant header in Utils.py.
    */
      function chancellorVoteNo() {
        // vote no on chancellor
        hideAllExcept(["miscEntryText"]); // text will be updated on next await_vote header
        /*
        BEGIN QUESTION 2
      */
        send("player_voted", JSON.stringify({ secret, id, vote: "nein" }));
      }

      // do the appropriate action when a card is pressed
      function pressedCard(ind) {
        // if an action should be taken
        if (cardClickState != 0) {
          // get the card that is being discarded
          const discarded = currentCards[ind];
          // remove that card from the cards to choose from
          currentCards.splice(ind, 1);
          // if president is discarding
          if (cardClickState == 1) {
            // don't let another button press resend the card
            cardClickState = 0;
            send(
              "president_discarded",
              JSON.stringify({
                secret,
                cards: currentCards,
                discarded,
              })
            );
          } else {
            // get the card left over (the policy that will be enacted)
            const card = currentCards[0];
            // don't let another button press resend the card
            cardClickState = 0;
            send(
              "chancellor_discarded",
              JSON.stringify({
                secret,
                card,
                discarded,
              })
            );
          }
        }
      }

      // end the policy peek power (called by the president)
      function endPolicyPeek() {
        send("end_policy_peek", JSON.stringify({secret}));
      }

      // president chooses a player to investigate
      function investigatePlayer(id) {
        send(
          "investigate_player",
          JSON.stringify({secret, player: id})
        );
      }

      // called after the president is done looking at a player's role
      function endInvestigatePlayer() {
        send("end_investigate_player", JSON.stringify({secret}));
      }

      // president picks who will be the next president
      function specialElection(id) {
        send(
          "special_election_pick",
          JSON.stringify({secret, player: id})
        );
      }

      // president determines who to execute
      function performExecution(id) {
        console.log(`${id} is being executed`);
        send(
          "perform_execution",
          JSON.stringify({secret, player: id})
        );
      }

      // chancellor performs the veto power
      function chancellorVeto() {
        send("chancellor_vetoed", JSON.stringify({secret}));
      }

      // president agrees with the veto
      function presidentVeto() {
        send("president_veto_answer", JSON.stringify({secret, veto: true}));
      }

      // president denies the veto
      function presidentNoVeto() {
        send("president_veto_answer", JSON.stringify({secret, veto: false}));
      }

      function display_players(players) {
        /*players is a list of [player names, followed by player identites {liberal, fascist, hitler, unknown}]
            the player list should appear in the order that the game is being played.*/
        //remove all elements on the game_canvas
        let game_canvas = document.getElementById("game_canvas");
        while (game_canvas.firstChild) {
          game_canvas.removeChild(game_canvas.firstChild);
        }
        //add all new elements!
        for (i = 1; i < players.length + 1; i++) {
          //set the class
          var newElement = document.createElement("portrait");
          //set the style
          newElement.setAttribute("style", "--i: " + i);
          //get the correct image
          var url = image_url_mappings[players[i - 1][2]];
          var buttonID = "selectPlayer" + players[i - 1][1];
          var placardID = "placardPlayerID" + players[i - 1][1];
          var iVotedID = "votePlayerID" + players[i - 1][1];
          var jaOrNeinID = "jaOrNeinID" + players[i - 1][1];
          var portraitID = "portraitID" + players[i - 1][1];

          //set the rest of the HTML tag
          newElement.innerHTML =
            `<img class="sheep" id="${portraitID}" src="${url}" alt="${players[i - 1][0]}" data-picked="false"/> ` +
            `<img src="${jaURL}" id="${jaOrNeinID}" class="ja-or-nein" style="display: none"/>` +
            `<img src="${iVotedURL}" id="${iVotedID}" alt="i voted" class="i_voted" style="display: none"/> ` +
            `<div class="name_card">${players[i - 1][0]}</div> ` +
            `<div id="${placardID}"" class="placard" style="display: none"></div> ` +
            `<button id="${buttonID}" type="button" class="btn btn-primary" style="display: none; margin: auto">Select</button>`;

          //finally append!
          game_canvas.appendChild(newElement);
          if (!allIDs.includes(buttonID)) {
            allIDs.push(buttonID);
          }
          if (!allIDs.includes(iVotedID)) {
            allIDs.push(iVotedID);
          }
          if (!allIDs.includes(jaOrNeinID)) {
            allIDs.push(jaOrNeinID);
          }
          //note that placardIds are not appended - we want persistant placards, that don't get hidden
        }
        //adjust the style for the overarching game_canvas div
        game_canvas.setAttribute(
          "style",
          "--m: " +
            players.length +
            "; --tan: " +
            Math.tan(Math.PI / players.length).toFixed(2)
        );
      }

      /*
           Makes select buttons on top of a player visible for all players
           in `players`, a list of ids. On click of these buttons, performs `method`. Each button has an id of the format: `selectPlayer<id>`
           where <id> can be replaced by a player id. Each method takes in a
           single argument, the player id.
           This function can be used, for example, when a president needs to
           choose the chancellor and can only select certain players.
           */
      function display_player_buttons(players, method) {
        players.forEach((player, index) => {
          var button = document.getElementById(`selectPlayer${player}`);
          button.style.display = "block";
          button.setAttribute("onclick", `${method}('${player}')`);
        });
      }

      function set_placards(president, chancellor = undefined) {
        clear_placards();
        var p_placard = document.getElementById(`placardPlayerID${president}`);
        p_placard.innerText = "President";
        p_placard.style.display = "inline-block";
        if (chancellor) {
          var c_placard = document.getElementById(
            `placardPlayerID${chancellor}`
          );
          c_placard.innerText = "Chancellor";
          c_placard.style.display = "inline-block";
        }
      }

      function clear_placards() {
        Object.keys(idToName).forEach((id) => {
          var placard = document.getElementById(`placardPlayerID${id}`);
          placard.style.display = "none";
        });
      }

      function show_votes(players) {
        clear_votes();
        players.forEach((player) => {
          var vote_sticker = document.getElementById(`votePlayerID${player}`);
          vote_sticker.style.display = "block";
        });
      }

      function clear_votes() {
        Object.keys(idToName).forEach((id) => {
          var vote = document.getElementById(`votePlayerID${id}`);
          vote.style.display = "none";
        });
      }

      function show_highlight(nominee) {
        clear_highlights();
        var portraitID = "portraitID" + nominee;
        document.getElementById(portraitID).dataset.picked = "true";
      }

      function clear_highlights() {
        Object.keys(idToName).forEach((id) => {
          var portrait = document.getElementById(`portraitID${id}`);
          portrait.dataset.picked = "false";
        });
      }

      function show_failed_elections(failed_elections) {
        for (var i = 1; i <= 3; i++) {
          var circle = document.getElementById(`electionID${i}`);
          circle.dataset.filled = i <= failed_elections ? "true" : "false";
        }
      }

      function show_jas_neins(jas, neins) {
        clear_jas_neins();
        jas.forEach((player) => {
          let el = document.getElementById(`jaOrNeinID${player}`);
          el.src = jaURL;
          el.style.display = "block";
        });
        neins.forEach((player) => {
          let el = document.getElementById(`jaOrNeinID${player}`);
          el.src = neinURL;
          el.style.display = "block";
        });
      }

      function clear_jas_neins() {
        Object.keys(idToName).forEach((id) => {
          var el = document.getElementById(`jaOrNeinID${id}`);
          el.style.display = "none";
        });
      }

      function display_powers(powers) {
        /*Will add the presidential powers to the game board
        - powers, a 2d array of the powers on each tile
      */
        for (i = 1; i < 6; i++) {
          var mapping;
          if (powers[i - 1].length == 2) {
            mapping = "execution+veto";
            document.getElementById("fascist power " + i).src =
              power_url_mappings[mapping];
            document.getElementById("fascist power " + i).style.display =
              "block";
          } else if (powers[i - 1].length == 1) {
            mapping = powers[i - 1][0];
            document.getElementById("fascist power " + i).src =
              power_url_mappings[mapping];
            document.getElementById("fascist power " + i).style.display =
              "block";
          }
        }
      }

      function updateCards(liberal, fascist) {
        /*Will make this many of each type of card appear as played on the field!
         */
        for (i = 0; i < liberal; i++) {
          document.getElementById("liberal card " + (i + 1)).style.display =
            "block";
        }
        for (i = 0; i < fascist; i++) {
          document.getElementById("fascist card " + (i + 1)).style.display =
            "block";
        }
      }

      function startNewGame() {
        // call shepherd to_setup
        send("next_stage");
        // redirect
      }

      function refreshFacts() {
        fetch("https://uselessfacts.jsph.pl/random.json?language=en").then(r => r.json()).then(r => {
            console.log("fact: " + r.text);
            document.getElementById("fact-text").innerText = r.text;
        });
      }
