from typing import Dict, Union
import enum

from komidabot.messages import Trigger
from komidabot.users import User, UserId


class ActionResult(enum.Enum):
    ACCEPTED = 1  # Action was consumed, do no further processing
    DEFER = 2  # Defer action until a later time
    NOT_SUPPORTED = 3  # Action is not supported


# TODO: Revise this entire class from the start
class ConversationManager:
    def __init__(self):
        self.active_conversations = dict()  # type: Dict[UserId, Conversation]

    def __contains__(self, user: 'Union[User, UserId]'):
        if isinstance(user, User):
            return self.__contains__(user.id)
        elif not isinstance(user, UserId):
            raise TypeError()

        return user in self.active_conversations

    def __setitem__(self, user: 'Union[User, UserId]', conversation: 'Conversation'):
        if isinstance(user, User):
            return self.__setitem__(user.id, conversation)
        elif not isinstance(user, UserId):
            raise TypeError()

        return self.set_conversation(user, conversation, True)

    def set_conversation(self, user: 'UserId', conversation: 'Conversation', notify=True):
        if isinstance(user, User):
            return self.set_conversation(user.id, conversation, notify=notify)
        elif not isinstance(user, UserId):
            raise TypeError()

        if notify and user in self:
            pass  # TODO: Notify

        self.active_conversations[user] = conversation

    def __getitem__(self, user: 'Union[User, UserId]'):
        if isinstance(user, User):
            return self.__getitem__(user.id)
        elif not isinstance(user, UserId):
            raise TypeError()

        return self.active_conversations[user]

    def __delitem__(self, user: 'Union[User, UserId]'):
        if isinstance(user, User):
            return self.__delitem__(user.id)
        elif not isinstance(user, UserId):
            raise TypeError()

        if user in self:
            pass  # TODO: Notify

        del self.active_conversations[user]


class Conversation:
    def __init__(self, user: User):
        self.user = user

    def conversation_started(self, trigger: Trigger):
        raise NotImplementedError()

    def conversation_ended(self):
        raise NotImplementedError()

    def stop_conversation(self):
        # TODO: Implement class that has common interface with conversation manager and add an instance field to handle
        #  this without special casing too much
        pass

    def trigger_received(self, trigger: Trigger) -> ActionResult:
        raise NotImplementedError()
