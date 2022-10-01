<img align="right" src="readmefigures/PiE_Sheep.png" alt="PiE Sheep" width="86" height="135">

# Shepherd Secret Hitler Onboarding

Join the liberals and discover the wolves in sheep's clothing, or help the fascists pull the wool over everyone's eyes!

### Getting Started

Hopefully you have been to the git tutorial by now. If you haven't, please talk to Adam, Sam, Jon!

First you need to fork this repository. You will do this by clicking on fork in the upper right corner of github.

![Fork button](readmefigures/Fork_button.png)

This will give you a copy of this repo for your own use. Only one person per group needs to fork this repo. Next you will need to add your partner(s) to your repo, which you can do by clicking on settings at the top bar of your newly created repo, going to manage access, and adding collaborators.

![Fork button](readmefigures/Settings_button.png)

Lastly, you will need to clone the new repo onto your computer. Copy the link at the top right of the page:

![Download button](readmefigures/Download_button.png)

and run `git clone <link>`. You can also optionally run `TODO`

## About the Project

Welcome to Sheep-ret (Secret?) Hitler! You will be implementing a web version of the party game Secret Hitler that mimics Shepherd's infrastructure.

If you haven't already played IRL, you should first acquaint yourself with the [rules](https://secrethitler.com/assets/Secret_Hitler_Rules.pdf) of the game.

You will be writing code in three files: Shepherd.py, server.py and templates/game.html. In order for the game to fully operate, you will have to implement parts of the following functions. We have broken these down into three phases and recommend completing each phase separately, but you are free to move around.

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
3. templates/game.html
   1. `chancellor_request`
   2. `chancellorVoteYes` and `chancellorVoteNo`

### Phase 1

**Shepherd.py**

1. `start_game`
2. `player_joined_ongoing_game`
3. `to_chancellor`

**templates/game.html**

1. `socket.on chancellor_request`
2. `chancellorVoteYes and chancellorVoteNo`

After you have completed this phase, you should be able to start a game and the chancellor should be able to vote!

### Phase 2

**server.py**

1. `player_voted`
2. `president_discarded`

**templates/game.html**

3. `display_player_buttons`

**Shepherd.py**

4. `receive_vote`
5. `president_discarded`
6. `investigate_player`

### Phase 3

7. `call_special_election`

## General Tips and Instructions

To run the game, open up three seperate terminals and cd into the shepherd folder for all terminals with the command `cd shepherd`. Then enter `python3 server.py`, `python3 -m ydl`, and `python3 shepherd.py` each in separate terminals. You should see the messages

```
Hello, world!
Running server on port 5000. Pages:  
        http://localhost:5000/index.html
        http://localhost:5000/game.html
```

which mean that the server, ydl, and shepherd is up and running! Go to localhost:5000 in the browser to play your game!

To debug your code, use `print` statements in `.py` files, which display in the terminal, or `console.log` statements in `.html` files, which you can view in your browser using `right click -> Inspect`. `Shepherd.py` also prints information about the game state in the terminal whenever it receives a header, which you can change in the `diagnostics` function.

## About Shepherd

### Welcome to Shepherd

You probably know the gist of what you've gotten into, so now we are going to talk some specifics.

Shepherd is the field control software that PiE uses / maintains to get the game running. In short, Shepherd is a framework that facilitates communication between a variety of important programs that are working together to run the game. Shepherd's second (and equally important task) is to serve as an automated referee, keeping track of all the scores, timers, and rules for the game.

### Shepherd's parts

A typical year's Shepherd system might look like the following block diagram (don't worry, we are going to break it down):

![Typical Shepherd Block Diagram](readmefigures/Typical_Shepherd_Block_Diagram.png)

So really all of Shepherd's parts fall into a few categories:

- State Machine
- Front End Interfaces
- Servers
- Supporting backend utilities

It's worth noting that all communication flows through the central state machine, and that many of the peripheral programs are stateless (they don't remember anything).

Shepherd is designed to run asynchronously. That means that each part of Shepherd is running in its own thread and is unaffected by a slowdown or crash that happens in another part (in theory). Therefore we need a method of communication that can send data from one part of Shepherd to another.

Here we have the same diagram as before, colored to show the form of communication used:

![Shepherd Communication](readmefigures/Shepherd_Communication.png)

Here each of the greyed out blocks is initialized in its own thread.

- Red lines represent communication performed via YDL.

  This is a module that we wrote that is used to send data between two threads on the same machine in a file called YDL.py. There is a lot more to know about Shepherd's use of YDL, but we will cover that later.

- Green lines represent communication via SocketIO and Proto Buffs, which is similar in functionality to JSON but is much lighter weight. SocketIO is used to pack these protobufs into tcp packets to send to the robots.
- Orange lines represent communication via SocketIO and JSON. We use these two libraries to communicate with other computers on the internet (or often just on the same WIFI network).
- Blue lines represent communication via the serial ports of the computer. This is used to communicate with [Arduinos](https://en.m.wikipedia.org/wiki/Arduino), which we use to power our field sensors. We use the runtime-maintained dev_handler and lowcar projects to handle this communication, and those cython files are wrapped by our python sensors_interface.py. In a nutshell, a lowcar message can be sent between an arduino and shepherd to update the value of a variable on the arduino, or report a value.
- Black lines represent communication via a function call. This means that the two blocks shown are not running in separate threads and can simply be called / data returned normally.

Now, we are going to dive a little into the nitty gritty of how the state machine works. Feel free to skip to the next section.

As you've probably noticed, the main part of the state machine is Shepherd.py, however this file doesn't exist in a vacuum. Lets look at the helper files first:

- [utils.py](https://github.com/pioneers/shepherd/blob/master/utils.py) is perhaps the most important periphery. This file first and foremost defines the targets and headers that YDL uses to tie shepherd together (more on that below). This file also defines constants that are widely used in the code, and should be easy to find / change. There are also quite a few ENUMs that are defined in Utils.py, however these are not really python enums, just unique strings that serve the same purpose. Lastly, Utils.py defines the various timers that shepherd uses.

- On the subject of timers, we come to [timer.py](https://github.com/pioneers/shepherd/blob/master/timer.py). This file contains a class Timer, which takes a `timer_type` enum from Utils.py, and creates a new timer object that can be later initialized with a duration using `timer.start_timer(durration)`. You can check if these timers are still running using the `timer.is_running()` function, as well as reset them with `timer.reset()` or `Timer.reset_all()`. Each of these timer instances will spawn a new thread, so that they can run un-interrupted, and if specified they will send an YDL message when they finish.

  The timer type enum in Utils.py is a dictionary with the following arguments:

  - TYPE, a unique string used to identify the timer_type.
  - FUNCTION, the empty YDL header to be sent to Shepherd.py when the timer runs out. Leave unset to not send a YDL message at all.

- [alliance.py](https://github.com/pioneers/shepherd/blob/master/alliance.py) defines the Alliance class, which is responsible for holding information about an alliance such as the teams in the alliance, and the color of the alliance, as well as game-specific data for the alliance such as a score variable, which is subject to change each year.

- [sheet.py](https://github.com/pioneers/shepherd/blob/master/sheet.py) handles communication with a google sheet used for recording match scores and is populated with that day's match data. If no internet connection can be established, it will discard the scored rather than write them and it will pull match data from a downloaded CSV, the path to which is defined in Utils.py

- [coding_challenge_problems.py](https://github.com/pioneers/shepherd/blob/master/coding_challenge_problems.py) is a file that is subject to frequent change, however it will always be used to generally handle the auto-grading of student coding challenges.

- [ydl.py](https://github.com/pioneers/shepherd/blob/master/ydl.py) is a that handles the YDL communication in shepherd. YDL.py must be run in order to launch the YDL server, and then YDL communication is possible. YDL is written by shepherd, and is the successor to a difficult library called LCM. If you see the name 'LCM' in any shepherd documentation, know that it has been replaced by YDL.

- Audio.py, bot.py, and runtime_manager.py all have important uses, but are not finalized enough to be worth mentioning here.

Lastly, lets talk about Shepherd.py. It might be useful to read the section on YDL before reading this, or you might want to read this section twice.

[shepherd.py](https://github.com/pioneers/shepherd/blob/master/shepherd.py) is structured as follows:

- YDL queue and dispatch loop, which translates YDL requests to function calls, taking into account the GAME_STATE global variable as well as the given header. This uses the set of dictionaries found at the bottom of the file.

  YDL queues can be started via `ydl_start_read(target, queue)`, where target is the YDL target that this queue will receive messages from, and queue is a python Queue where those events will be stored. The event object is structured as `[header, args]`.

  YDL events may be sent using `ydl_send(target, header, args)`, where args is a dictionary of argument names and values. Explicitly filling in the values for this function is considered bad coding practice in shepherd, and you should instead use the syntax `ydl_send(*HEADER(**kwargs))` where `HEADER` is a header that you can call in `utils.py` and `**kwargs` is the keyword arguments to that header (ie. `SEND_SCORE(blue=1, gold=2)`).

- Evergreen functions, which are functions often invoked via YDL that are needed every year. These include the functions such as to_auto, which helps advance the game state, score keeping functions, information sharing functions, and a reset function.

- Game specific functions, which are also typically called via YDL, but are subject to change based on the current game. These are typically the functions responsible for implementing the rules of the game and serving as a referee.

- YDL header mappings, which are a collection of dictionaries that translate YDL headers to functions. There is one of these dictionaries for each game state, and when an event is processed by the dispatch loop, it will use the dictionary corresponding to the current game state. It is important to note that a header can map to different functions depending on the current game state, and that a function may be mapped to by multiple headers.

- Evergreen variables, which are global variables that will be used every year.

- Game specific variables, which are global variables that are subject to change each year.

### How Shepherd uses YDL

Please refer to the [updated ydl guide](https://github.com/pioneers/ydl/blob/main/docs/tutorial.md) for more details. The following guide below is outdated. 

YDL is used to send messages asynchronously throughout the shepherd backend. We use these messages to request a certain action to be performed by another program. When an YDL message is sent to a piece of shepherd, that message is stored in a queue, where it will be processed in a FIFO (first in first out) order. Thus, there is constantly a queue of incoming requests that dictate the actions that our programs must take. When a message is pulled off the queue, it is dispatched via some dispatching code and runs the corresponding function.

- in Shepherd.py, this dispatching code uses dictionaries to map the YDL message to a function, which is then called. This method is not needed for the other smaller and simpler server files.

![YDL Diagram](readmefigures/YDL_Diagram.png)

A YDL message is structured as a target, then a header, and then a body of arguments, which is typically a dictionary. YDL message:

`[TARGET][HEADER][ARGUMENTS]`

The YDL targets and headers are defined in the Utils.py file, and are instrumental to the function of YDL. Each target represents a receiving queue, while the header is used to indicate to the dispatching code which function to invoke.

A YDL message telling the scoreboard what stage the game is in might be sent as follows:

```
from YDL import ydl_send
from Utils import *

ydl_send(*SCOREBOARD_HEADER.STAGE("stage"=GAME_STATE))
```

It is important to use an appropriate header, and to name all the arguments in the header with the correct name.

## Shepherd Onboarding Project

That was a ton of information to handle, so in order to bring you up to speed, we are going to have you use the Shepherd framework to implement the game [Secret Hitler](https://secrethitler.com), [rules](https://secrethitler.com/assets/Secret_Hitler_rules.pdf), while using a much simpler version of Shepherd.

### Shepherd Changes

To begin with, the version of Shepherd we will be using for this project has been stripped down to just the bare essentials:

![Shepherd Onboarding Block Diagram](readmefigures/Shepherd_Onboarding_Block_Diagram.png)

Phew! That's a lot easier to look at. Here we have just a state machine, a single server, and a single front-end webpage.

### Credit

Secret Hitler is not our creation! That credit goes to Mike, Tommy, Max, and Mac at [secrethitler.com](https://secrethitler.com). We are making no attempt to make money from the game, and our work falls under the original Creative Commons License (BY-NC-SA 4.0) that the game was released with. You can find that license [here](https://CreativeCommons.org/licenses/by-nc-sa/4.0/legalcode).
