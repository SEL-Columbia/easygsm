# test/test.py

from twisted.internet import reactor

from datetime import datetime
import os.path, sys, random

sys.path.append(os.path.abspath('.')) # really, nothing better?
from serialmodem.lib.protocol import tmpSerialPort,SerialModemProtocol

class Telit(SerialModemProtocol):

    init_sequence = [
        "ATE0", # command echo disabled
        "AT", 
        "AT+CMEE=2", # verbose debug
        "AT#BND=3", # North America
        "AT#AUTOBND=2", # quad-band
        "AT+CNMI=2,1,0,0,0" # setup sms indicator
        ]

    def __init__(self, mode, new_message_handler):
        SerialModemProtocol.__init__(self, 
                                     self.init_sequence, 
                                     mode,
                                     new_message_handler,
                                     process_unread_messages=True,
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

    def __init__(self, mode, new_message_handler):
        SerialModemProtocol.__init__(self,
                                     self.init_sequence, 
                                     mode,
                                     new_message_handler,
                                     stagger_sends=False,
                                     send_interval=(4,10)
                                     )

class Test(object):
    
    protocol = None
    count = 0

    def send_alert(self, label, phone_numbers):
        for i in range(1,5):
            for phone_number in phone_numbers:
                self.protocol.send_sms(
                    phone_number, 
                    "%s:alert %d: %s" % (
                        label, Test.count, str(datetime.now())))
            Test.count += 1
                
        reactor.callLater(60, self.send_alert, label, phone_numbers)
    
    def got_message(self, messages):
        for message in messages:
            print "got message:", message.parts["TEXT"]

if __name__ == "__main__":
    args = sys.argv[1:]
    device = args[0]
    br = int(args[1]) # baudrate
    mode = int(args[2])
    label = args[3]
    phone_numbers = args[4:]
    
    # test message form
    from serialmodem.lib import message
    desc = "+CMGL: 1,1,"",23"
    body = "07914140540500F8040B913174999472F000001120205140720A04F4F29C0E"
    m = message.Message(0, desc, body)
    print m.parts
    print
    desc = '+CMGL: 1,"REC READ","+13479949270","","11/02/02,15:04:27-20"'
    body = "test"
    m = message.Message(1, desc, body)
    print m

    # test protocol
    t = Test()
#m = Multitech(mode, getattr(t, got_message))
    m = Telit(mode, t.got_message)
    t.protocol = m
    ser = tmpSerialPort(m, device, reactor, baudrate=br, timeout=1)
    
    reactor.callLater(2, t.send_alert, label, phone_numbers)
    
    reactor.run()

