from Utils import *


def start():
    global payload
    if payload != EMPTY_PAYLOAD:
        # do action
        print(payload)
    payload = EMPTY_PAYLOAD


###########################################
# Evergreen Variables
###########################################

GAME_STATE = STATE.GAME_OVER

###########################################
# LCM Simulator
###########################################

EMPTY_PAYLOAD = []

payload = EMPTY_PAYLOAD


def lcm_send(load):
    global payload
    payload = load
