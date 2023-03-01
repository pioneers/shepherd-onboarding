# Mini-project 2: Ping-Pong

How do shepherds communicate with each other? By yodeling. In this mini-project you will learn how to yodel well.


## Part 1: Send and receive

Open up 3 terminals (you can do "split terminal" in VSCode). In the first terminal, run
```
python3 -m ydl
```
In the second terminal, run
```
python3 po.py
```
Now, you can run `python3 pi.py` in the third terminal. A message should appear in the first terminal. 
If you want to stop the first two terminals, press `Ctrl C` in each of them.

__Question 1__: What does first terminal say?

__Task 1__: Modify `pi.py` such that `po.py` receives the message `("PO", "Goats eat blueberries")`.

__Task 2__: Modify `po.py` such that instead of listening indefinitely, it will stop running after receiving 5 messages.


## Part 2: Real communication

In your 3 terminals, run:

Terminal 1: `python3 -m ydl`
Terminal 2: `python3 pong.py`
Terminal 3: `python3 ping.py`

Now, `ping.py` should prompt you for a message. Send the message `shepherd` and see what happens!

__Question 2__: What are other messages you can send to get a canned response back? Which file stores the dictionary of possible responses?

__Task 3__: Add a custom message + canned response pair.

__Task 4__: Right now, all `pong.py` does is sometimes send responses back. However, `ping.py` is hard of hearing, so sometimes we would like `pong.py` to repeat what it last said, which is what the repeat header is for. Fill in `respond_to_repeat()` such that `pong.py` can repeat the last response sent.

__Task 5__: Usually, communication between `ping.py` and `pong.py` is civilized. However, a user of `ping.py` might send nasty and hurtful messages to `pong.py`. We want `pong.py` to "ban" `ping.py` if such a message is sent. A list of banned messages can be found in `utils.py`; if `ping.py` sends such a message, have `pong.py` stop sending any messages (even repeats) to `ping.py`.

__Task 6__: How fast is YDL? It's written in python, so by computing standards, it's probably pretty slow. Notice that whenever `pong.py` sends a message, it also sends the time that the message was sent. In `ping.py`, fill in code to print how long a response message took to send through YDL.



