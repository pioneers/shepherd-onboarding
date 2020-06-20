import Shepherd
import server
from Utils import LCM_TARGETS

def lcm_send(target_channel, header, args={}): # pylint: disable=dangerous-default-value
    """
    Send header and dictionary to target channel (string)
    """

    if target_channel == LCM_TARGETS.SHEPHERD:
        Shepherd.LCM_receive(header, args)
    elif target.channel == LCM_TARGETS.SERVER:
    	Server.LCM_receive(header, args)