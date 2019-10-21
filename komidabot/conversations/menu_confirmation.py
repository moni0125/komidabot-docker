# TODO: Deprecated

import enum

from komidabot.conversation import *


class State(enum.Enum):
    pass  # TODO: Statecharts? PyPDEVS? Hans?


class MenuConfirmationConversation(Conversation):
    def __init__(self, partner: MessageReceiver, parse_result):
        super().__init__(partner)
        self.parse_result = parse_result
        self.state = None  # TODO: Figure this out

    def on_conversation_started(self, starting_message: ReceivedMessage = None):
        # Conversation does not depend on a starting message -> ignore starting_message

        self.partner.send_text_message('Menu confirmation initiated')

    def on_conversation_stopped(self, conversation: 'Conversation' = None, forced=False):
        if forced:
            self.partner.send_text_message('Menu confirmation stopped (forced)')
        else:
            self.partner.send_text_message('Menu confirmation stopped')

    def on_message_received(self, message: ReceivedMessage):
        self.conversation_finished()

    def on_other_conversation(self, other: 'Conversation'):
        raise RuntimeError('Cannot start other conversation')
