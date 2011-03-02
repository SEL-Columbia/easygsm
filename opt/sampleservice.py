# opt/sampleservice.py

from twisted.application import internet, service
from twisted.internet import protocol, reactor
from twisted.web import client, resource, server

import sys, os.path
sys.path.append(os.path.abspath('.')) # really, nothing better?

from easygsm.lib.serialmodem import tmpSerialPort
import modems, webmin, ipfwd, irc

class SampleService(service.Service):

    modem = None

    ipfwd_enabled = False

    irc_enabled = False
    irc = None

    def startService(self):
        log.msg("starting service")
        service.Service.startService(self)

    def stopService(self):
        log.msg("stopping service")
        if not self.mode.sms_terminated:
            self.modem.sendLine(chr(26))
        service.Service.stopService(self)

    def got_sms(self, messages):
        for message in messages:
            if self.ipfwd_enabled:
                pass
            if self.irc_enabled:
                pass
            print "got_sms:", message
    
    def sent_sms(self, message_index):
        print "sent_sms", message_index

def makeService(config):

    ser = service.MultiService()

    # service
    s = SampleService()

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

    # webmin on port 9191
    if config.get("webmin_enabled"):
        e = webmin.Webmin()
        e.modem = s.modem
        w = internet.TCPServer(config.get("webmin_port", 9191), 
                               server.Site(e))
        w.setServiceParent(ser)

    # ip forwarding
    if config.get("ipfwd_enabled"):
        agent = client.Agent(reactor)
        s.ipfwd_enabled = True
        s.ipfwd_get_frequency = config.get("ipfwd_get_frequency")
        s.ipfwd_server = config.get("ipfwd_server")
        s.ipfwd_send_uri = config.get("ipfwd_send_uri")
        s.ipfwd_get_uri = config.get("ipfwd_get_uri")
        s.ipfwd_got_uri = config.get("ipfwd_got_uri")

    # irc client 
    if config.get("irc_enabled"):
        s.irc_enabled = True
        i = protocol.ReconnectingClientFactory()
        i.protocol = irc.IRCBot
        s.irc = i.protocol
        i.nickname = config.get("irc_nick")
        i.channel = config.get("irc_channel")
        i.send_sms = s.modem.send_sms
        irc_service = internet.TCPClient(config.get("irc_server"), 
                                         config.get("irc_port", 6667),
                                         i)
        irc_service.setServiceParent(ser)

    return ser

