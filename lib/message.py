# lib/message.py

from messaging.sms import SmsDeliver

class Message(object):

    modes = (0, 1)
    
    def __init__(self, mode, description, body):
        if mode not in self.modes:
            raise ValueError("Invalid sms mode: %s" % (mode,))

        self._mode = mode
        self._description = description
        self._body = body
        self._parts = {}
        self._parse()

    def __str__(self):
        el = [self._description, self._body]
        el.extend(
            ["%s = %s" % (k,v) for k,v in self._parts.iteritems()])
        return '\n'.join(el)

    @property
    def parts(self):
        """Returns the relevant parts of the message object."""
        return self._parts

    def _parse(self):
        self._parts["MODE"] = self._mode

        desc = self._description.split(':', 1)[1].strip()

        if self._mode == 1:
            index, status, number, name, timestamp = desc.split(',', 4)
            self._parts["INDEX"] = int(index.strip())
            self._parts["STATUS"] = status.strip()
            self._parts["NUMBER"] = number.strip()
            self._parts["NAME"] = name.strip()
            self._parts["TIMESTAMP"] = timestamp.strip()
            self._parts["TEXT"] = self._body.strip()

        elif self._mode == 0:
            index, status, name, length = desc.split(',')
            self._parts["INDEX"] = int(index.strip())
            self._parts["STATUS"] = status.strip()
            self._parts["NAME"] = name.strip()
            self._parts["LENGTH"] = int(length.strip())

            pdu = self._body.strip()
            sms = SmsDeliver(pdu)
            self._parts["PDU"] = pdu
            self._parts["NUMBER"] = sms.number
            self._parts["TEXT"] = sms.text

