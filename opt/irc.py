# opt/irc.py

from twisted.words.protocols import irc

class IRCBot(irc.IRCClient):

    def connectionMade(self):
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        self.msg(channel, 
                 "Hello %s, I'll be your modem server today." % (channel,))

    def userJoined(self, user, channel):
        self.msg(channel, "Hi "+user+", I'll be your unlimited SMS server today.")

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "Umm, let's talk in the main channel, shall we?"
            self.msg(user, msg)

        # Otherwise check to see if it is a message directed at me
        elif msg.startswith(self.nickname):
            response = ""
            m = [m for m in msg.split(' ') if m]
            command = m[1:]
            if len(command) > 2 and command[0] == "send":
                recipient = command[1]
                text = ' '.join(command[2:])
                self.factory.send_sms(recipient, text)
                response = "%s: ask %s to check for the message - '%s'." % (user, recipient, text)
            else:
                response = "%s? I'm just a bot... please be more specific." % (' '.join(command),)

            self.msg(channel, response)
