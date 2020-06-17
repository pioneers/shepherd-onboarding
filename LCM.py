import Shepherd
from Utils import LCM_TARGETS

def lcm_send(target_channel, header, dic={}): # pylint: disable=dangerous-default-value
    """
    Send header and dictionary to target channel (string)
    """

    if target_channel == LCM_TARGETS.SHEPHERD:
        Shepherd.LCM_receive(header, dic)
