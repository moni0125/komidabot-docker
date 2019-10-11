from collections import namedtuple
import functools
from typing import Dict

from flask import current_app as app

from komidabot.messages import MessageHandler, Message

UserId = namedtuple('UserId', ['id', 'provider'])


class UserManager:  # TODO: This probably could use more methods
    def get_user(self, user_id: UserId, **kwargs) -> 'User':
        raise NotImplementedError()

    def get_subscribed_users(self):
        raise NotImplementedError()

    def get_message_handler(self, user: 'User') -> MessageHandler:
        raise NotImplementedError()  # TODO: Figure out if this needs to be per person or for multicasting purposes


class User:  # TODO: This probably needs more methods
    @property
    def id(self) -> UserId:
        raise NotImplementedError()

    def get_locale(self):  # TODO: Properly look into this
        raise NotImplementedError()

    def is_admin(self):
        user_id = self.id
        return (user_id.provider, user_id.id) in app.config.get('ADMIN_IDS', [])

    @property
    def manager(self) -> UserManager:
        raise NotImplementedError()

    def get_message_handler(self) -> MessageHandler:
        return self.manager.get_message_handler(self)

    def send_message(self, message: 'Message'):
        return self.get_message_handler().send_message(self, message)


class UnifiedUserManager(UserManager):
    def __init__(self):
        self._managers = dict()  # type: Dict[str, UserManager]

    def register_manager(self, provider: str, manager: UserManager):
        if provider in self._managers:
            raise ValueError('Multiple managers registered for one provider')
        if isinstance(manager, UnifiedUserManager):
            raise ValueError('Cannot register the unified user manager')

        self._managers[provider] = manager

    def get_user(self, user_id: UserId, **kwargs) -> 'User':
        if user_id.provider not in self._managers:
            raise ValueError('Unknown user provider')

        return self._managers[user_id.provider].get_user(user_id, **kwargs)

    def get_subscribed_users(self):
        return functools.reduce(list.__add__, [manager.get_subscribed_users() for manager in self._managers.values()])

    def get_message_handler(self, user: 'User') -> MessageHandler:
        return user.manager.get_message_handler(user)
