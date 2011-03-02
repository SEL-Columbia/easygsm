# opt/ipfwd.py

from twisted.internet import protocol
from twisted.web.http_headers import Headers

from stringprod import StringProducer

from collections import deque
from datetime import datetime
import json, sys, random, uuid 

class IpForward(protocol.Protocol):
    pass

class IpForwardFactory(protocol.ReconnectingClientFactory):
    pass

