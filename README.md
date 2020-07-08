# Shepherd Secret Hitler Onboarding

![Image of Shepherd Secret Hitler](https://github.com/pioneers/shepherd-onboarding/blob/master/assets/Shepherd%20Secret%20Hitler.png)

Right now this is just the PM solution, there will probably be a new skeleton code branch here in the future and a branch for all the onboarding groups

Join the liberals and discover the wolves in sheep's clothing, or help the fascists pull the wool over everyone's eyes!

## Shepherd
### Welcome to Shepherd
You probably know the gist of what you've gotten into, so now we are going to talk some specifics.
Shepherd is the field control software that PiE uses / maintains to get the game running. In short shepherd is a framework that facilitates communication between a variety of important programs that are working together to run the game. Shepherds second (and equally important task) is to serve as an automated referee, keeping track of all the scores, timers, and rules for the game.

### Shepherd's parts
A typical year's shepherd system might look like the following block diagram (don't worry, we are going to break it down):
![Typical Shepherd Block Diagram](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Typical%20Shepherd%20Block%20Diagram.png)
So really all of shepherd's parts fall into a few categories:
  * State Machine
  * Front End Interfaces
  * Servers
  * Supporting backend utilities

It is worth noting that all communication flows through the central state machine, and that many of the peripheral programs are stateless (they don't remember anything)

Shepherd is designed to run asynchronously. That means that each part of shepherd is running in its own thread and is unaffected by a slowdown or crash that happens in another part (in theory). Therefore that we need a method of communication that can send data from one part of shepherd to another.
Here we have the same diagram as before, colored to show the form of communication used:
![Shepherd Communication](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Shepherd%20Communication.png)
Here each of the greyed out blocks is initialized in it's own thread.
  * Red lines represent communication performed via LCM.
   
    This is a library that is used to send data between two threads on the same machine and we have wrapped it in a file called LCM.py. There is a lot more to know about Shepherd's use of LCM, and we will cover that later.
  * Green lines represent communication via Proto Buffs (this is new to shepherd this year), which is similar in functionality to JSON but is much lighter weight.
  * Orange lines represent communication via SocketIO and JSON. We use these two libraries to communicate with other computers on the internet (or often just on the same WIFI network).
  * Blue lines represent communication via the serial ports of the computer. This is used to communicate with [Ardiunos](https://en.m.wikipedia.org/wiki/Arduino), which we use to power our field sensors.
  * Black lines represent communication via a function call. This means that the two blocks shown are not running in separate threads and can simply be called / data returned normally.

### How Shepherd uses LCM
queues
targets and headers
examples
TODO

## Shepherd Onboarding Project
That was a ton of information to handle, so in order to bring you up to speed, we are going to have you use the shepherd framework to implement the game [Secret Hitler](https://secrethitler.com), [rules](https://secrethitler.com/assets/Secret_Hitler_rules.pdf), while using a much simpler version of shepherd.

### Shepherd Changes
To begin with, the version of Shepherd we will be using for this project has been stripped down to just the bare essentials:
![Shepherd Onboarding Block Diagram](https://github.com/pioneers/shepherd-onboarding/blob/master/readmefigures/Shepherd%20Onboarding%20Block%20Diagram.png)
Phew! That's a lot easier to look at. Here we have just a state machine, a single server, and a single front end webpage.
LCM changes:
 * LCM is really hard to install (maybe impossible on windows?) and since we are creating such a simple game which does not require asynchronous pieces, we dropped the LCM communication altogether. That being said, since we want you to get used to communication via LCM, we have instead included a pseudo LCM implementation in LCM.py. This exposes almost the same functionality to the user, with the notable exception that its just a glorified function call.
 * Using our pseudo LCM for communication between the server and the state machine will teach you how the real LCM is used. In order to follow that abstraction, you should refrain from ever calling a function in the state machine from the server, or vice versa.
 * Lastly, normal LCM is asynchronous, which means once you send an LCM message, your code will immediately move on to the next line. Because our pseudo LCM is nothing more than a glorified function call, the code will instead pause and process whatever your LCM message was intended to do. Therefore, you should take care not to get stuck in a recursive loop of LCM calls.

### Using Github
Hopefully you have been to the git tutorial by now. If you haven't, please talk to Alex or Akshit!
First you need to clone this repository
Use git Issues...
TODO

### Your Task
TODO
