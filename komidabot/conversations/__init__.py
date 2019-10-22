from typing import Dict, Optional, Type, Union
import enum

from komidabot.messages import Trigger
from komidabot.users import User, UserId


# TODO: Add a way to save and load conversations?


class ActionResult(enum.Enum):
    ACCEPTED = 1  # Trigger was consumed, do no further processing
    DEFER = 2  # Defer trigger until a later time
    NOT_SUPPORTED = 3  # Trigger is not supported
    NO_CONVERSATION = 4  # Trigger was not consumed because there was no active conversation


class IConversationManagerBase:
    def __contains__(self, conversation: 'Conversation'):
        raise NotImplementedError()

    def conversation_stop(self, conversation: 'Conversation'):
        raise NotImplementedError()

    def get_active_conversation(self, user: 'Union[User,UserId]') -> 'Optional[Conversation]':
        raise NotImplementedError()

    def trigger_received(self, user: 'Union[User,UserId]', trigger: Trigger) -> ActionResult:
        raise NotImplementedError()


class ConversationManager(IConversationManagerBase):
    def __init__(self):
        self.active_conversations = dict()  # type: Dict[UserId, Conversation]

    def __contains__(self, conversation: 'Conversation'):
        if not isinstance(conversation, Conversation):
            raise TypeError()

        user_id = conversation.user.id
        if user_id not in self.active_conversations:
            return False

        user_conversation = self.active_conversations[user_id]
        if user_conversation == conversation:
            return True
        elif isinstance(user_conversation, IConversationManagerBase):
            return conversation in user_conversation
        else:
            return False

    def conversation_stop(self, conversation: 'Conversation'):
        if not isinstance(conversation, Conversation):
            raise TypeError()

        user_id = conversation.user.id
        if user_id not in self.active_conversations:
            raise ValueError()

        user_conversation = self.active_conversations[user_id]
        if user_conversation == conversation:
            del self.active_conversations[user_id]
        elif isinstance(user_conversation, IConversationManagerBase):
            user_conversation.conversation_stop(conversation)
        else:
            raise ValueError()

    def get_active_conversation(self, user: 'Union[User,UserId]') -> 'Optional[Conversation]':
        if isinstance(user, User):
            return self.get_conversation(user.id)
        elif not isinstance(user, UserId):
            raise TypeError()

        if user not in self.active_conversations:
            return None

        conversation = self.active_conversations[user]

        if isinstance(conversation, IConversationManagerBase):
            return conversation.get_active_conversation(user)
        return conversation

    def trigger_received(self, user: 'Union[User,UserId]', trigger: Trigger) -> ActionResult:
        conversation = self.get_conversation(user)

        if conversation is None:
            return ActionResult.NO_CONVERSATION

        result = conversation.trigger_received(user, trigger)
        # TODO: Handle different results
        return result

    def initiate_conversation(self, conversation_type: 'Type[Conversation]', user: 'Union[User,UserId]',
                              *args, **kwargs):
        print('{}, {}, {}, {}'.format(conversation_type, user, args, kwargs))
        conversation = conversation_type(user, self, *args, **kwargs)
        self.set_conversation(user, conversation)

    def get_conversation(self, user: 'Union[User,UserId]') -> 'Optional[Conversation]':
        if isinstance(user, User):
            return self.get_conversation(user.id)
        elif not isinstance(user, UserId):
            raise TypeError()

        return self.active_conversations.get(user, None)

    def set_conversation(self, user: 'Union[User,UserId]', conversation: 'Conversation'):
        if isinstance(user, User):
            return self.set_conversation(user.id, conversation)
        elif not isinstance(user, UserId):
            raise TypeError()

        self.active_conversations[user] = conversation


class Conversation:
    def __init__(self, user: User, manager: IConversationManagerBase, *args, **kwargs):
        self.user = user
        self.manager = manager

    def conversation_started(self, trigger: Trigger):
        raise NotImplementedError()

    def conversation_ended(self):
        raise NotImplementedError()

    def stop_conversation(self):
        self.manager.conversation_stop(self)

    def trigger_received(self, user: 'Union[User,UserId]', trigger: Trigger) -> ActionResult:
        raise NotImplementedError()
