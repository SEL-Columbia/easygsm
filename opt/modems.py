# opt/modems.py

import sys, os.path
sys.path.append(os.path.abspath('.')) # really, nothing better?

from serialmodem.lib.protocol import SerialModemProtocol

class Telit(SerialModemProtocol):

    init_sequence = [
        "ATE0", # command echo disabled
        "AT", 
        "AT+CMEE=2", # verbose debug
        "AT#BND=3", # North America
        "AT#AUTOBND=2", # quad-band
        "AT+CNMI=2,1,0,0,0" # setup sms indicator
        ]

    def __init__(self, mode=1, gsc=None, ssc=None):
        SerialModemProtocol.__init__(self, 
                                     self.init_sequence, 
                                     mode,
                                     got_sms_callback=gsc,
                                     sent_sms_callback=ssc,
                                     process_unread_messages=False,
                                     delete_existing_messages=True,
                                     stagger_sends=False,
                                     send_interval=(0,0)
                                     )

class Multitech(SerialModemProtocol):

    init_sequence = [
        "ATE0", # command echo disabled
        "AT", 
        "AT+CNMI=2,1,0,0,0" # setup message indicator
        ]

    def __init__(self, mode=1, gsc=None, ssc=None):
        SerialModemProtocol.__init__(self,
                                     self.init_sequence, 
                                     mode=1,
                                     got_sms_callback=gsc,
                                     sent_sms_callback=ssc,
                                     stagger_sends=False,
                                     send_interval=(4,10)
                                     )

