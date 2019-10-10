from komidabot.facebook.received_message import ReceivedTextMessage
from komidabot.messages import Trigger


class Bot:
    # FIXME: Deprecated
    def message_received_legacy(self, message: ReceivedTextMessage):
        raise NotImplementedError

    def trigger_received(self, trigger: Trigger):
        raise NotImplementedError
