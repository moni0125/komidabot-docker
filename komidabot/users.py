from collections import namedtuple
import datetime
import functools
from typing import Dict, List, Optional

from flask import current_app as app

import komidabot.messages as messages
import komidabot.models as models

UserId = namedtuple('UserId', ['id', 'provider'])


class UserManager:  # TODO: This probably could use more methods
    def get_user(self, user_id: UserId, **kwargs) -> 'User':
        raise NotImplementedError()

    def get_subscribed_users(self) -> 'List[User]':
        # FIXME: Use days
        raise NotImplementedError()

    def initialise(self):
        raise NotImplementedError()


class User:  # TODO: This probably needs more methods
    @property
    def id(self) -> UserId:
        return UserId(self.get_internal_id(), self.get_provider_name())

    def get_provider_name(self) -> 'str':
        raise NotImplementedError()

    def get_internal_id(self) -> 'str':
        raise NotImplementedError()

    def get_db_user(self) -> 'Optional[models.AppUser]':
        user_id = self.id
        return models.AppUser.find_by_id(user_id.provider, user_id.id)

    def get_locale(self) -> 'Optional[str]':  # TODO: Properly look into this
        user = self.get_db_user()

        return user.language

    def get_campus_for_day(self, date: datetime.date) -> 'Optional[models.Campus]':
        user = self.get_db_user()
        day = models.Day(date.isoweekday())

        return user.get_campus(day)

    def is_admin(self):
        user_id = self.id
        return user_id in app.config.get('ADMIN_IDS', [])

    def is_feature_active(self, feature_id: str):
        user = self.get_db_user()
        return models.Feature.is_user_participating(user, feature_id)

    @property
    def manager(self) -> UserManager:
        return self.get_manager()

    def get_manager(self) -> UserManager:
        raise NotImplementedError()

    def get_message_handler(self) -> messages.MessageHandler:
        raise NotImplementedError()

    def send_message(self, message: 'messages.Message'):
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
        # FIXME: Use days
        return functools.reduce(list.__add__, [manager.get_subscribed_users() for manager in self._managers.values()])

    def initialise(self):
        for manager in self._managers.values():
            manager.initialise()
