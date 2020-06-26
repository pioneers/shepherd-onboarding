from Utils import LCM_TARGETS

CHANNEL_MAPPINGS = {}

def lcm_send(target_channel, header, args={}): # pylint: disable=dangerous-default-value
    """
    Send header and dictionary to target channel (string)
    """
    global CHANNEL_MAPPINGS

    if target_channel in CHANNEL_MAPPINGS.keys():
        CHANNEL_MAPPINGS[target_channel](header, args)
    else:
        print("# WARNING! header:", header, "was dropped because the target", target_channel, "was not registered")

def lcm_register(target_channel, function):
    global CHANNEL_MAPPINGS
    CHANNEL_MAPPINGS[target_channel] = function
    print("# Pseudo-LCM: channel", target_channel, "registered")
