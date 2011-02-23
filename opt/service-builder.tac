# opt/service-builder.tac
# eg: twistd -ny service-builder.tac

from twisted.application import service
from twisted.python import log, logfile

import sys, os.path
sys.path.append(os.path.abspath('.')) # really, nothing better?

from easygsm.opt import sampleservice

options = { "devmodem": "/dev/ttyUSB0", # modem port
	    "modem_mode": 1, # 0 - PDU, 1 - TEXT
            "baudrate": 9600, # modem baudrate
            "timeout": 1, # modem timeout, in seconds
            "eth_iface": "192.168.1.101", # ethernet interface
	    "webmin_enabled": False,
            "webmin_port": 9191, # listener port for webmin access
	    "ipfwd_enabled": False,
	    "ipfwd_put_uri": "google.com",
	    "ipfwd_get_uri" :"google.com",
	    "irc_enabled": True,
	    "irc_server": "irc.freenode.net",
	    "irc_channel": "sharedsolar",
	    "irc_nick": "loweryourbills",
	    "irc_port": 6667 }

logfile = logfile.LogFile("simpleservice.log", "/tmp", maxRotatedFiles=10)
ser = sampleservice.makeService(options)
application = service.Application('service')
application.setComponent(log.ILogObserver, log.FileLogObserver(logfile).emit)
ser.setServiceParent(service.IServiceCollection(application))
