from flask import current_app as app

from komidabot.facebook.received_message import ReceivedMessage
from komidabot.message_receiver import MessageReceiver


class Conversation:
    def __init__(self, partner: MessageReceiver):
        self.partner = partner

    @staticmethod
    def initiate_conversation(conversation: 'Conversation', starting_message: ReceivedMessage = None):
        # TODO: This REALLY shouldn't be part of the facebook package
        app.messenger.start_conversation(conversation, starting_message=starting_message)

    def conversation_finished(self):
        # TODO: This REALLY shouldn't be part of the facebook package
        app.messenger.end_conversation(self)

    def on_conversation_started(self, starting_message: ReceivedMessage = None):
        raise NotImplementedError()

    def on_conversation_stopped(self, conversation: 'Conversation' = None, forced=False):
        raise NotImplementedError()

    def on_message_received(self, message: ReceivedMessage):
        raise NotImplementedError()

    def on_other_conversation(self, other: 'Conversation'):
        raise NotImplementedError()

    # TODO: Add a way to save and load conversations?
