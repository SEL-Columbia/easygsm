# opt/webmin.py

from twisted.web import resource
import cgi

class ModemLogs(resource.Resource):

    isLeaf = True

    def __init__(self, modem):
        resource.Resource.__init__(self)
        self.modem = modem

    def render_GET(self, request):
        response = ["<html><body>",
                    "<h3>Outgoing</h3>",
                    '<table border="1">',
                    "".join(["<tr><td>%s</td></tr>" % row \
                                 for row in self.modem.outgoing]),
                    "</table>",
                    "<h3>Incoming</h3>",
                    '<table border="1">',
                    "".join(["<tr><td>%s</td></tr>" % row \
                                 for row in self.modem.incoming]),
                    "</table>",
                    "</body></html>"]
        return "".join(response)

class SMSLogs(resource.Resource):

    isLeaf = True

    def __init__(self, modem):
        resource.Resource.__init__(self)
        self.modem = modem

    def render_GET(self, request):
        x = self.modem.sent
        y = self.modem.received
        xlen = len(x)
        ylen = len(y)
        if xlen > ylen:
            y += ' ' * (xlen - ylen)
        elif ylen > xlen:
            x += ' ' * (ylen - xlen)

        response = ["<html><body>",
                    "<h3>SMS Logs</h3>",
                    '<table border="1" width="100%">',
                    '<tr><td width="50%" align="center"><b>Sent</b></td><td width="50%" align="center"><b>Received</b></td></tr>',
                    "".join(["<tr><td>%s</td><td>%s</td></tr>" % (x,y) \
                                 for x,y in zip(x,y)]),
                    "</table>",
                    "</body></html>"]
        return "".join(response)

class Logs(resource.Resource):

    def __init__(self, modem):
        resource.Resource.__init__(self)
        self.modem = modem

    def getChild(self, link, request):
        if link == "modem":
            return ModemLogs(self.modem)
        elif link == "sms":
            return SMSLogs(self.modem)
        else:
            return self

    def render_GET(self, request):
        response = ["<html><body>",
                    "<ul>",
                    '<li><a href="logs/modem">Modem Logs</a></li>',
                    '<li><a href="logs/sms">SMS Logs</a></li>',
                    "</ul>",
                    "</body></html>"]
        return "".join(response)

class Webmin(resource.Resource):
    
    def __init__(self, modem):
        resource.Resource.__init__(self)
        self.modem = modem

    def getChild(self, link, request):
        if link == "logs":
            return Logs(self.modem)
        else:
            return self

    def render_GET(self, request):
        response = ["<html><body>",
                    '<ul><li><a href="logs">Logs</a></li></ul>',
                    "</body></html>"]
        return "".join(response)

