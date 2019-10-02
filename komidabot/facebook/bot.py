from komidabot.facebook.received_message import ReceivedPostbackMessage, ReceivedTextMessage
from komidabot.messages import *


# TODO: This should not be part of the facebook package
class Bot:
    def message_received_legacy(self, message: ReceivedTextMessage):
        raise NotImplementedError

    def postback_received_legacy(self, message: ReceivedPostbackMessage):
        raise NotImplementedError

    def trigger_received(self, trigger: Trigger):
        raise NotImplementedError
