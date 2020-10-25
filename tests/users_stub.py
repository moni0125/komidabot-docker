from typing import Dict, List
from typing import Union

import komidabot.menu
import komidabot.messages as messages
import komidabot.users as users
from komidabot.models import AppUser, Menu
from komidabot.subscriptions.daily_menu import CHANNEL_ID as DAILY_MENU_ID

PROVIDER_ID = 'stub'


class UserManager(users.UserManager):
    def __init__(self):
        self.users: 'Dict[users.UserId, User]' = dict()

        self.message_handler = MessageHandler()

    def add_user(self, internal_id: str, locale: str = 'nl') -> 'User':
        user_id = users.UserId(internal_id, PROVIDER_ID)

        if user_id in self.users:
            raise ValueError('Duplicate user ID')

        user = User(self, user_id.id)
        self.users[user_id] = user

        user.add_to_db()
        user.get_db_user().set_language(locale)

        return user

    def get_user(self, user: 'Union[users.UserId, AppUser]', **kwargs) -> 'User':
        if isinstance(user, AppUser):
            user = users.UserId(user.internal_id, user.provider)

        if not isinstance(user, users.UserId):
            raise ValueError()

        if user not in self.users:
            raise ValueError('Invalid user ID: {}'.format(user))

        return self.users[user]

    def initialise(self):
        assert False  # Does not get called

    def get_identifier(self):
        return PROVIDER_ID


class User(users.User):
    def __init__(self, manager: UserManager, internal_id: str):
        self._manager = manager
        self._id = internal_id

    def get_provider_name(self) -> 'str':
        return PROVIDER_ID

    def get_internal_id(self) -> 'str':
        return self._id

    def supports_subscription_channel(self, channel: str) -> bool:
        return channel in [DAILY_MENU_ID]

    def get_manager(self) -> UserManager:
        return self._manager

    def get_message_handler(self):
        if self._manager.message_handler is None:
            raise NotImplementedError()
        return self._manager.message_handler


class MessageHandler(messages.MessageHandler):
    """Message handler that stores messages in a user->messages dictionary"""

    def __init__(self):
        self.message_log: Dict[users.UserId, List[str]] = dict()

    def reset(self):
        self.message_log = dict()

    def send_message(self, user, message: messages.Message) -> messages.MessageSendResult:
        if user.id.provider != PROVIDER_ID:
            raise ValueError('User id is not for Stub Provider')

        if isinstance(message, messages.TextMessage):
            if user.id not in self.message_log:
                self.message_log[user.id] = []

            text = message.text

            self.message_log[user.id].append(text)

            return messages.MessageSendResult.SUCCESS
        elif isinstance(message, messages.MenuMessage):
            if user.id not in self.message_log:
                self.message_log[user.id] = []

            text = komidabot.menu.get_menu_text(message.menu, message.translator, user.get_locale())

            self.message_log[user.id].append(text)

            return messages.MessageSendResult.SUCCESS
        elif isinstance(message, messages.SubscriptionMenuMessage):
            if user.id not in self.message_log:
                self.message_log[user.id] = []

            campus = user.get_campus_for_day(message.date)
            menu = Menu.get_menu(campus, message.date)

            text = komidabot.menu.get_menu_text(menu, message.translator, user.get_locale())

            self.message_log[user.id].append(text)

            return messages.MessageSendResult.SUCCESS
        else:
            return messages.MessageSendResult.UNSUPPORTED
