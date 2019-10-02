from typing import Dict
from komidabot.conversation import Conversation, ReceivedMessage


class ConversationManager:
    def __init__(self):
        # TODO: Keys for this dict would need to allow multiple conversation sources
        self.active_conversations = dict()  # type: Dict[str, Conversation]

    def handle_message_conversation(self, message: ReceivedMessage):
        user_id = message.sender.get_id()  # type: str

        if user_id in self.active_conversations:
            # There's an active conversation, route the message to it
            self.active_conversations[user_id].on_message_received(message)
            return True

        return False

    def start_conversation(self, conversation: Conversation, starting_message: ReceivedMessage = None):
        user_id = conversation.partner.get_id()  # type: str

        if user_id in self.active_conversations:
            # There's already an active conversation, notify the current conversation
            self.active_conversations[user_id].on_other_conversation(conversation)
        else:
            self.active_conversations[user_id] = conversation
            conversation.on_conversation_started(starting_message=starting_message)

    def replace_conversation(self, conversation: Conversation, replacement: Conversation):
        raise NotImplementedError()

    def end_conversation(self, conversation: Conversation):
        user_id = conversation.partner.get_id()  # type: str

        if user_id in self.active_conversations:
            if self.active_conversations[user_id] is conversation:
                conversation.on_conversation_stopped()
                del self.active_conversations[user_id]
            else:
                self.active_conversations[user_id].on_conversation_stopped(conversation)
        else:
            pass  # TODO: Handle?
