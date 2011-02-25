# opt/sampleservice.py

from twisted.application import internet, service
from twisted.internet import protocol, reactor
from twisted.web import resource, server

import sys, os.path
sys.path.append(os.path.abspath('.')) # really, nothing better?

from easygsm.lib.serialmodem import tmpSerialPort
import modems, webmin, irc

class SampleService(service.Service):

    modem = None

    def startService(self):
        log.msg("starting service")
        service.Service.startService(self)

    def stopService(self):
        log.msg("stopping service")
        service.Service.stopService(self)

    def got_sms(self, messages):
        for message in messages:
            print "got_sms:", message
    
    def sent_sms(self, message_index):
        print "sent_sms", message_index

def makeService(config):
    ser = service.MultiService()

    # service
    s = SampleService()

    # webmin on port 9191
    w = internet.TCPServer(9191, server.Site(webmin.Webmin(s.modem)))
    w.setServiceParent(ser)

    # modem 
    m = tmpSerialPort(modems.Telit(mode=config.get("modem_mode", 1), 
                                   gsc=s.got_sms,
                                   ssc=s.sent_sms),
                      config["devmodem"],
                      reactor,
                      baudrate=config.get("baudrate", 9600),
                      timeout=config.get("timeout", 0))

    # modem access for the service
    s.modem = m.protocol 

    # ip forwarding
    if config["ipfwd_enabled"]:
        pass

    # ircclient 
    if config["irc_enabled"]:
        i = protocol.ReconnectingClientFactory()
        i.protocol = irc.IRCBot
        i.nickname = config["irc_nick"]
        i.channel = config["irc_channel"]
        i.send_sms = s.modem.send_sms
        irc_service = internet.TCPClient(config["irc_server"], 
                                         config.get("irc_port", 6667),
                                         i)
        irc_service.setServiceParent(ser)

    return ser

