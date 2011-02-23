# lib/serialmodem.py

from twisted.internet import defer, threads
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver

from messaging.sms import SmsSubmit, SmsDeliver
import message

from collections import deque
import random, types

def _sink(dummy):
    return

class tmpSerialPort(SerialPort):
    """Remove IFF: python-twisted >= 10.2"""
    def connectionLost(self, reason):
        SerialPort.connectionLost(self, reason)
        self.protocol.connectionLost(reason)

class SerialModemProtocol(LineReceiver):

    modes = (0, 1) # 0 - PDU, 1 - TEXT

    message_status = ((0, "REC UNREAD"),
                      (1, "REC READ"),
                      (2, "STO UNSENT"),
                      (3, "STO SENT"),
                      (4, "ALL"))

    def __init__(self, 
                 init_sequence, 
                 mode=0, 
                 got_sms_callback=_sink, 
                 sent_sms_callback=_sink,
                 process_unread_messages=False,
                 delete_existing_messages=False, 
                 stagger_sends=False, 
                 send_interval=(0,0)):

        self._init_sequence = init_sequence

        self.mode = mode
        self._init_sequence.append("AT+CMGF=%d" % (mode,))

        # callback on new message arrival
        if not callable(got_sms_callback):
            raise ValueError(
                "invalid got_sms_callback: %s" % (got_sms_callback,))
        self._got_sms_callback = got_sms_callback
        
        # callback on message send
        if not callable(sent_sms_callback):
            raise ValueError(
                "invalid sent_sms_callback: %s" % (sent_sms_callback,))
        self._sent_sms_callback = sent_sms_callback

        # pre-processing of existing messages
        self._process_unread_messages = process_unread_messages
        self._delete_existing_messages = delete_existing_messages

        # staggered send controls
        self._stagger_sends = stagger_sends
        self._send_interval = send_interval

        self._waiting = False # AT command sent, awaiting response
        self._reading = False # new messages being read

        # for tracking an unterminated message
        self._outgoing_message_terminated = True

    @property
    def outgoing(self):
        """Returns the queue of all lines to be sent to the modem."""
        return self._outgoing

    @property
    def incoming(self):
        """Returns the queue of all response lines from the modem."""
        return self._incoming

    @property
    def received(self):
        """Returns the queue of lines resulting from a AT+CMGL."""
        return self._received_log

    @property
    def sent(self):
        """Returns the queue of messages sent."""
        return self._sent

    @property
    def waiting(self):
        """Returns the wait state of the modem."""
        return self._waiting

    @property
    def reading(self):
        """Returns the read state of the modem."""
        return self._reading

    @property
    def outgoing_message_terminated(self):
        """Returns the state of the outgoing messages, whether 
        it was terminated with a ctrl-z or not."""
        return self._outgoing_message_terminated

    def _set_mode(self, mode):
        if mode and not mode in self.modes:
            raise ValueError("invalid mode: %s", (mode,))
        self._mode = mode
    mode = property(lambda self: self._mode, _set_mode)

    def connectionMade(self):
        """
        Called when a connection has been made with the modem. The modem 
        is now ready to receive AT commands. You can opt to include 
        initialization actions here (for eg: delete messages stored on the
        SIM, process unread messages, etc.)
        """
        self._outgoing = deque(self._init_sequence, maxlen=255)
        self._incoming = deque(maxlen=255)
        self._received = deque(maxlen=255)
        self._sent = deque(maxlen=255)
        self._received_log = deque(maxlen=255)

        if self._process_unread_messages:
            self.list_sms(0) # process unread messages

        if self._delete_existing_messages:
            self.delete_sms(1, 4) # delete all messages on SIM

        self._write_next() # let's begin

    def connectionLost(self, reason):
        print "connection lost: %s" % reason

    def rawDataReceived(self, data):
        if data:
            if "+CMTI" in data: # new message arrived in the middle of a send
                tmp = data
                plus = tmp.find('+')
                tmp[plus:tmp.find('\n', plus)].strip()
                self._incoming.append(tmp)

                self.list_sms(0) # list unread sms messages

            if '>' in data: # send message with trailing ctrl-z
                self.setLineMode()
                sms_text = self.outgoing[0][1]
                print sms_text
                self._sent.append(sms_text)
                self._outgoing_message_terminated = False
                self.sendLine(sms_text + chr(26))
                self._outgoing_message_terminated = True

    def lineReceived(self, line):
        if line:
            print line
            self._incoming.append(line)

            if "OK" in line:
                self._waiting = False
                _prev = self._outgoing[0]

                if type(_prev) == types.TupleType:
                    threads.deferToThread(self._sent_sms_callback, _prev[2])

                elif self._reading:
                    self._reading = False
                    if _prev.startswith("AT+CMGL"):
                        """
                        Compromise:
                        Better to pop the message from the SIM
                        *after* the callback is completed, but 
                        the callback is most likely third-party and 
                        not guaranteed to return, so I do it last here.
                        """
                        d = self._received_sms()
                        d.addCallback(self._sim_delete)
                        d.addCallback(
                            lambda m: threads.deferToThread(
                                self._got_sms_callback, m))

                self._outgoing.popleft() # moving along now
                
                if self._stagger_sends and self.outgoing:
                    # If the following AT command is also a SMS send,
                    # delay its sending.
                    if _prev.startswith("AT+CMGS") and \
                            _prev.startswith("AT+CMGS"):
                        t = random.randint(self._send_interval[0],
                                           self._send_interval[1])
                        reactor.callLater(t, self._write_next)
                else:
                    self._write_next()

            elif "ERROR" in line:
                self._waiting = False
                self._reading = False
                self._outgoing.extendleft(reversed(self._init_sequence))
                self._write_next()

            elif "+CMTI" in line: # new sms indicator
                self.list_sms(0) # list unread sms messages

            elif self._reading:
                self._received.append(line)
                self._received_log.append(line)

    def _write_next_old(self):
        if not self._waiting and self._outgoing:
            message = self._outgoing[0]
            print message
            self.sendLine(message)
            self._waiting = True
            self._sent.append(message)

            if message.startswith("AT+CMGS"): # send sms
                self.setRawMode()
            elif message.startswith("AT+CMGL"):
                self._reading = True

    def _write_next(self):
        if not self._waiting and self._outgoing:
            if type(self._outgoing[0]) == types.TupleType: # send sms
                message = self._outgoing[0][0]
                self.sendLine(message)
                self.setRawMode()
            else:
                message = self._outgoing[0]
                self.sendLine(message)
                if message.startswith("AT+CMGL"):
                    self._reading = True

            print message
            self._waiting = True
            self._sent.append(message)

    def _received_sms(self):
        """Returns a deferred - list of message objects received."""
        messages = deque(maxlen=255)
        while self._received:
            info = self._received.popleft()
            if info.startswith("+CMGL"):
                sms_body = []
                while self._received:
                    line = self._received[0]
                    if line.startswith("+CMGL"):
                        break
                    else:
                        sms_body.append(line)
                        self._received.popleft()
                messages.append(
                    message.Message(self.mode, info, '\n'.join(sms_body)))
        return defer.succeed(messages)

    def _sim_delete(self, messages):
        """
        Returns a deferred - list of message objects after 
        queueing message delete commands for the modem.
        """
        for message in messages:
            index = message.parts["INDEX"]
            self._outgoing.append("AT+CMGD=%d,%d" % (index, 0))
        return defer.succeed(messages)

    def list_sms(self, code):
        """Send an AT+CMGL for unread messages to the modem."""
        message = 'AT+CMGL="%s"' % (self.message_status[code][1],) if \
            self.mode == 1 else "AT+CMGL=%d" % (code,)

        if not self._reading and message not in self._outgoing:
            self._outgoing.append(message)
            self._write_next()

    def send_sms(self, number, text, callback_index=None):
        if self.mode == 0:
            sms = SmsSubmit(number, text)
            pdu = sms.to_pdu()[0]
            message_list = [("AT+CMGS=%d" % (pdu.length,), 
                             pdu.pdu,
                             callback_index)]
        else:
            message_list = [("AT+CMGS=%s" % (number,), 
                             text,
                             callback_index)]
        
        self._outgoing.extend(message_list)
        self._write_next()

    def delete_sms(self, message_index, delete_type=0):
        """
        Delete types:
            0 - Delete message at message_index
            1 - Delete all messages leaving unread and sent/unsent messages
            2 - Delete all read and sent messages leaving unread and unsent
            3 - Delete all messages except unread (including unsent messages)
            4 - Delete all messages
        """
        self._outgoing.append("AT+CMGD=%d,%d" % (message_index, delete_type))
        self._write_next()

    def switch_mode(self):
        """Switches modem between TEXT and PDU modes."""
        self.mode = 1 if self.mode == 0 else 0
        self._init_sequence.pop()
        self._init_sequence.append("AT+CMGF=%d" % (self.mode,))

    def soft_reset(self):
        """Clear the queues and re-initialize the modem."""
        self._outgoing.clear()
        self._incoming.clear()
        self._received.clear()
        self._sent.clear()
        self._waiting = False
        self._reading = False
        self._outgoing.extend(self._init_sequence)        
        self._write_next()
