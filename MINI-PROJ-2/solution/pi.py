"""
The sending half of the pi / po introduction. This file will send one message
to po.
"""
from ydl import ydl_send, ydl_start_read

# sends a header (BLUEBERRY) and dictionary to the target (PO)
# any file that's listening to the target PO will receive this message. 
#
# This is nice and simple; however, hard-coding headers as strings is really
# error prone (what if we mistype the header? it'll be sent just fine, but 
# then the receiving end might crash). That's why in the next section,
# we'll introduce an alternative syntax for creating messages to send. 
ydl_send("PO", "BLUEBERRY", {"info": "Goats eat blueberries"})
