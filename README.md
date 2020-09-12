<img align="right" src="https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/PiE%20Sheep.png" alt="PiE Sheep" width="86" height="135">

# Shepherd Secret Hitler Onboarding
Join the liberals and discover the wolves in sheep's clothing, or help the fascists pull the wool over everyone's eyes!

### Getting Started
Hopefully you have been to the git tutorial by now. If you haven't, please talk to Alex or Akshit!

First you need to fork this repository. You will do this by clicking on fork in the upper right corner of github.

![Fork button](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Fork%20button.png)

This will give you a copy of this repo for your own use. Only one person per group needs to fork this repo. Next you will need to add your partner(s) to your repo, which you can do by clicking on settings at the top bar of your newly created repo, going to manage access, and adding collaborators.

![Fork button](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Settings%20button.png)

Lastly, you will need to clone the new repo onto your computer. Copy the link at the top right of the page:

![Download button](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Download%20button.png)

 and run `git clone <link>`. You can also optionally run `TODO`


## About the Project
Welcome to Sheep-ret (Secret?) Hitler! You will be implementing a web version of the party game Secret Hitler that mimics Shepherd's infrastructure.

If you haven't already played IRL, you should first acquaint yourself with the [rules](https://secrethitler.com/assets/Secret_Hitler_Rules.pdf) of the game.

You will be writing code in three files:  Shepherd.py, server.py and templates/game.html. In order for the game to fully operate, you will have to implement parts of the following functions. We have broken these down into three phases and recommend completing each phase separately, but you are free to move around.

1. Shepherd.py
    1. `start_game`
    2. `player_joined_ongoing_game`
    3. `to_chancellor`
    4. `receive_vote`
    5. `president_discarded`
    6. `investigate_player`
    7. `call_special_election`
2. server.py
    1. `player_voted`
    2. `president_discarded`
3. game.html
    1. `chancellor_request`
    2. `chancellorVoteYes` and `chancellorVoteNo`

### Phase 1
**Shepherd.py**
1. `start_game`
2. `player_joined_ongoing_game`
3. `to_chancellor`

**game.html**
1. `socket.on chancellor_request`
2. `chancellorVoteYes and chancellorVoteNo`

After you have completed this phase, you should be able to start a game and the chancellor should be able to vote!

### Phase 2
**server.py**
1. `player_voted`
2. `president_discarded`

**game.html**

3. `display_player_buttons`

**Shepherd.py**

4. `receive_vote`
5. `president_discarded`
6. `investigate_player`

### Phase 3
7. `call_special_election`

You may write the functions in whatever order you like, but we would recommend that you work in order for each file (e.g. solve 1.1 before 1.2).

To run the game, enter `python3 server.py` in the terminal. You should see the messages
```
# Pseudo-LCM: channel lcm_target_server registered
# Pseudo-LCM: channel lcm_target_shepherd registered
```
which mean that the Pseudo-LCM is up and running!

To debug your code, use `print` statements in `.py` files, which display in the terminal, or `console.log` statements in `.html` files, which you can view in your browser using `right click -> Inspect`. `Shepherd.py` also prints information about the game state in the terminal whenever it receives a header, which you can change in the `diagnostics` function.

## About Shepherd
### Welcome to Shepherd
You probably know the gist of what you've gotten into, so now we are going to talk some specifics.

Shepherd is the field control software that PiE uses / maintains to get the game running. In short, Shepherd is a framework that facilitates communication between a variety of important programs that are working together to run the game. Shepherd's second (and equally important task) is to serve as an automated referee, keeping track of all the scores, timers, and rules for the game.

### Shepherd's parts
A typical year's Shepherd system might look like the following block diagram (don't worry, we are going to break it down):

![Typical Shepherd Block Diagram](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Typical%20Shepherd%20Block%20Diagram.png)

So really all of Shepherd's parts fall into a few categories:
  * State Machine
  * Front End Interfaces
  * Servers
  * Supporting backend utilities

It's worth noting that all communication flows through the central state machine, and that many of the peripheral programs are stateless (they don't remember anything).

Shepherd is designed to run asynchronously. That means that each part of Shepherd is running in its own thread and is unaffected by a slowdown or crash that happens in another part (in theory). Therefore we need a method of communication that can send data from one part of Shepherd to another.

Here we have the same diagram as before, colored to show the form of communication used:

![Shepherd Communication](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Shepherd%20Communication.png)

Here each of the greyed out blocks is initialized in its own thread.
  * Red lines represent communication performed via LCM.

    This is a library that is used to send data between two threads on the same machine and we have wrapped it in a file called LCM.py. There is a lot more to know about Shepherd's use of LCM, but we will cover that later.
  * Green lines represent communication via Proto Buffs (this is new to shepherd this year), which is similar in functionality to JSON but is much lighter weight.
  * Orange lines represent communication via SocketIO and JSON. We use these two libraries to communicate with other computers on the internet (or often just on the same WIFI network).
  * Blue lines represent communication via the serial ports of the computer. This is used to communicate with [Arduinos](https://en.m.wikipedia.org/wiki/Arduino), which we use to power our field sensors.
  * Black lines represent communication via a function call. This means that the two blocks shown are not running in separate threads and can simply be called / data returned normally.

Now, we are going to dive a little into the nitty gritty of how the state machine works. Feel free to skip to the next section.

As you've probably noticed, the main part of the state machine is Shepherd.py, however this file doesn't exist in a vacuum. Lets look at the helper files first:

  * [Utils.py](https://github.com/pioneers/shepherd/blob/master/Utils.py) is perhaps the most important periphery. This file first and foremost defines the targets and headers that LCM uses to tie shepherd together (more on that below). This file also defines constants that are widely used in the code, and should be easy to find / change. There are also quite a few ENUMs that are defined in Utils.py, however these are not really python enums, just unique strings that serve the same purpose. Lastly, Utils.py defines the various timers that shepherd uses.

  * On the subject of timers, we come to [Timer.py](https://github.com/pioneers/shepherd/blob/master/Timer.py). This file contains a class Timer, which takes a `timer_type` enum from Utils.py, and creates a new timer object that can be later initialized with a duration using `timer.start_timer(durration)`. You can check if these timers are still running using the `timer.is_running()` function, as well as reset them with `timer.reset()` or `Timer.reset_all()`. Each of these timer instances will spawn a new thread, so that they can run un-interrupted, and if specified they will send an LCM message when they finish.

    The timer type enum in Utils.py is a dictionary with the following arguments:

      * TYPE, a unique string used to identify the timer_type.
      * NEEDS_FUNCTION, a boolean that tells the timer class whether or not it should send an empty LCM message to Shepherd.py when the timer runs out.
      * FUNCTION, the LCM header to be sent if NEEDS_FUNCTION is true

  * [Alliance.py](https://github.com/pioneers/shepherd/blob/master/Alliance.py) defines the Alliance class, which is responsible for holding information about an alliance such as the teams in the alliance, and the color of the alliance, as well as game-specific data for the alliance such as a score variable, which is subject to change each year.

  * [Sheet.py](https://github.com/pioneers/shepherd/blob/master/Sheet.py) handles communication with a google sheet used for recording match scores and is populated with that day's match data. If no internet connection can be established, it will discard the scored rather than write them and it will pull match data from a downloaded CSV, the path to which is defined in Utils.py

  * [Code.py](https://github.com/pioneers/shepherd/blob/master/Code.py) is a file that is subject to frequent change, however it will always be used to implement the seed generation and solution generation of the coding challenges.

  * [LCM.py](https://github.com/pioneers/shepherd/blob/master/LCM.py) is a file that serves as a wrapper for LCM communication in shepherd. It is referenced by any file that engages in LCM communication.

  * Audio.py, bot.py, and runtime_manager.py all have important uses, but are not finalized enough to be worth mentioning here.

Lastly, lets talk about Shepherd.py. It might be useful to read the section on LCM before reading this, or you might want to read this section twice.

[Shepherd.py](https://github.com/pioneers/shepherd/blob/master/Shepherd.py) is structured as follows:

  * LCM queue and dispatch loop, which translates LCM requests to function calls, taking into account the GAME_STATE global variable as well as the given header. This uses the set of dictionaries found at the bottom of the file.

    LCM queues can be started via `lcm_start_read(target, queue)`, where target is the lcm target that this queue will receive messages from, and queue is a python Queue where those events will be stored. The event object is structured as `[header, args]`.

    LCM events may be sent using `lcm_send(target, header, args)`, where args is a dictionary of argument names and values.

  * Evergreen functions, which are functions often invoked via LCM that are needed every year. These include the functions such as to_auto, which helps advance the game state, score keeping functions, information sharing functions, and a reset function.

  * Game specific functions, which are also typically called via LCM, but are subject to change based on the current game. These are typically the functions responsible for implementing the rules of the game and serving as a referee.

  * LCM header mappings, which are a collection of dictionaries that translate LCM headers to functions. There is one of these dictionaries for each game state, and when an event is processed by the dispatch loop, it will use the dictionary corresponding to the current game state. It is important to note that a header can map to different functions depending on the current game state, and that a function may be mapped to by multiple headers.

  * Evergreen variables, which are global variables that will be used every year.

  * Game specific variables, which are global variables that are subject to change each year.

### How Shepherd uses LCM
LCM is used to send messages asynchronously throughout the shepherd backend. We use these messages to request a certain action to be performed by another program. When an LCM message is sent to a piece of shepherd, that message is stored in a queue, where it will be processed in a FIFO (first in first out) order. Thus, there is constantly a queue of incoming requests that dictate the actions that our programs must take. When a message is pulled off the queue, it is dispatched via some dispatching code and runs the corresponding function.

  * in Shepherd.py, this dispatching code uses dictionaries to map the LCM message to a function, which is then called. This method is not needed for the other smaller and simpler server files.

![LCM Diagram](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/LCM%20Diagram.png)

A LCM message is structured as a target, then a header, and then a body of arguments, which is typically a dictionary. LCM message:

`[TARGET][HEADER][ARGUMENTS]`

The LCM targets and headers are defined in the Utils.py file, and are instrumental to the function of LCM. Each target represents a receiving queue, while the header is used to indicate to the dispatching code which function to invoke.

A LCM message telling the scoreboard what stage the game is in might be sent as follows:

```
from LCM import *
from Utils import *

data = {"stage": GAME_STATE}
lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, data)
```

It is important to use an appropriate header, and to name all the arguments in the dictionary with the correct key.

## Shepherd Onboarding Project
That was a ton of information to handle, so in order to bring you up to speed, we are going to have you use the Shepherd framework to implement the game [Secret Hitler](https://secrethitler.com), [rules](https://secrethitler.com/assets/Secret_Hitler_rules.pdf), while using a much simpler version of Shepherd.

### Shepherd Changes
To begin with, the version of Shepherd we will be using for this project has been stripped down to just the bare essentials:

![Shepherd Onboarding Block Diagram](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Shepherd%20Onboarding%20Block%20Diagram.png)

Phew! That's a lot easier to look at. Here we have just a state machine, a single server, and a single front-end webpage.

LCM changes:
 * LCM is really hard to install (maybe impossible on Windows?) and since we are creating such a simple game which does not require asynchronous pieces, we dropped the LCM communication altogether. That being said, since we want you to get used to communication via LCM, we have instead included a pseudo LCM implementation in LCM.py. This exposes almost the same functionality to the user, with the notable exception that it's just a glorified function call.
 * Using our pseudo LCM for communication between the server and the state machine will teach you how the real LCM is used. In order to follow that abstraction, you should refrain from ever calling a function in the state machine from the server, or vice versa.
 * Lastly, normal LCM is asynchronous, which means once you send an LCM message, your code will immediately move on to the next line. Because our pseudo LCM is nothing more than a glorified function call, the code will instead pause and process whatever your LCM message was intended to do. Therefore, you should take care not to get stuck in a recursive loop of LCM calls.

### Credit

Secret Hitler is not our creation! That credit goes to Mike, Tommy, Max, and Mac at [secrethitler.com](https://secrethitler.com). We are making no attempt to make money from the game, and our work falls under the original Creative Commons License (BY-NC-SA 4.0) that the game was released with. You can find that license [here](https://CreativeCommons.org/licenses/by-nc-sa/4.0/legalcode).
