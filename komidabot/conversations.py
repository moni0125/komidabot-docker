from typing import Dict, Union
import enum

from komidabot.messages import Trigger
from komidabot.users import User, UserId


# TODO: Add a way to save and load conversations?


class ActionResult(enum.Enum):
    ACCEPTED = 1  # Action was consumed, do no further processing
    DEFER = 2  # Defer action until a later time
    NOT_SUPPORTED = 3  # Action is not supported


class IConversationManager:
    def conversation_stop(self, conversation: 'Conversation'):
        raise NotImplementedError()


class ConversationManager(IConversationManager):
    def __init__(self):
        self.active_conversations = dict()  # type: Dict[UserId, Conversation]

    def conversation_stop(self, conversation: 'Conversation'):
        raise NotImplementedError()

    def set_conversation(self, user: 'UserId', conversation: 'Conversation', notify=True):
        if isinstance(user, User):
            return self.set_conversation(user.id, conversation, notify=notify)
        elif not isinstance(user, UserId):
            raise TypeError()

        if notify and user in self:
            pass  # TODO: Notify

        self.active_conversations[user] = conversation


class Conversation:
    def __init__(self, user: User, manager: IConversationManager):
        self.user = user
        self.manager = manager

    def conversation_started(self, trigger: Trigger):
        raise NotImplementedError()

    def conversation_ended(self):
        raise NotImplementedError()

    def stop_conversation(self):
        self.manager.conversation_stop(self)

    def trigger_received(self, trigger: Trigger) -> ActionResult:
        raise NotImplementedError()
