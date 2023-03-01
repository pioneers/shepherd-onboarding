"""
The sending half of the pi / po introduction. This file will send one message
to po.
"""
from ydl import YDLClient

# sends a tuple ("PO", "I like cheese") to the channel PO
# the channel is always the first part of the tuple
# any file that's listening to the channel PO will receive this message. 
#
# This is nice and simple; however, hard-coding information as strings is really
# error prone (what if we mistype something?). That's why in the next section,
# we'll introduce an alternative syntax for creating messages to send. 
YC = YDLClient()
YC.send(("PO", "I like cheese"))
