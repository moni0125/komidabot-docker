import datetime
import functools
from collections import namedtuple
from typing import Dict, List, Optional, Union

import komidabot.messages as messages
import komidabot.models as models
from komidabot.app import get_app

UserId = namedtuple('UserId', ['id', 'provider'])


class UserManager:  # TODO: This probably could use more methods
    def get_user(self, user: 'Union[UserId, models.AppUser]', **kwargs) -> 'User':
        raise NotImplementedError()

    def get_subscribed_users(self, day: models.Day) -> 'List[User]':
        identifier = self.get_identifier()
        users = models.AppUser.find_subscribed_users_by_day(day, provider=identifier)

        return [self.get_user(UserId(user.internal_id, identifier)) for user in users]

    # TODO: REMOVE
    # TODO: This should only be a temporary thing
    # def get_users_with_no_subscriptions(self) -> 'List[User]':
    #     identifier = self.get_identifier()
    #     users = models.AppUser.find_users_with_no_subscriptions(provider=identifier)
    #
    #     return [self.get_user(UserId(user.internal_id, identifier)) for user in users]

    def initialise(self):
        raise NotImplementedError()

    def get_identifier(self) -> str:
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

    def add_to_db(self):
        user_id = self.id
        models.AppUser.create(user_id.provider, user_id.id, '')

    def get_locale(self) -> 'Optional[str]':  # TODO: Properly look into this
        user = self.get_db_user()
        if user is None:
            return None

        return user.language

    def get_campus_for_day(self, date: datetime.date) -> 'Optional[models.Campus]':
        user = self.get_db_user()
        if user is None:
            return None

        day = models.Day(date.isoweekday())

        return user.get_campus(day)

    def set_campus_for_day(self, campus: models.Campus, date: datetime.date):
        user = self.get_db_user()
        if user is None:
            return

        day = models.Day(date.isoweekday())
        sub = user.get_subscription(day)

        if sub is None:
            # Make new subscription and set it to enabled by default
            user.set_campus(day, campus, True)
        else:
            user.set_campus(day, campus)

    def get_subscription_for_day(self, date: datetime.date) -> 'Optional[models.UserSubscription]':
        user = self.get_db_user()
        if user is None:
            return None

        day = models.Day(date.isoweekday())

        return user.get_subscription(day)

    def is_admin(self):
        user_id = self.id
        return user_id in get_app().admin_ids

    def is_feature_active(self, feature_id: str) -> bool:
        return models.Feature.is_user_participating(self.get_db_user(), feature_id)

    @property
    def manager(self) -> UserManager:
        return self.get_manager()

    def get_manager(self) -> UserManager:
        raise NotImplementedError()

    def get_message_handler(self) -> messages.MessageHandler:
        raise NotImplementedError()

    def send_message(self, message: 'messages.Message'):
        return self.get_message_handler().send_message(self, message)

    def __repr__(self):
        user_id = self.id
        return 'User: {}/{}'.format(user_id.provider, user_id.id)


class UnifiedUserManager(UserManager):
    def __init__(self):
        self._managers = dict()  # type: Dict[str, UserManager]

    def register_manager(self, provider: str, manager: UserManager):
        if provider in self._managers:
            raise ValueError('Multiple managers registered for one provider')
        if isinstance(manager, UnifiedUserManager):
            raise ValueError('Cannot register the unified user manager')

        self._managers[provider] = manager

    def get_user(self, user: 'Union[UserId, models.AppUser]', **kwargs) -> 'User':
        if user.provider not in self._managers:
            raise ValueError('Unknown user provider')

        return self._managers[user.provider].get_user(user, **kwargs)

    def get_subscribed_users(self, day: models.Day):
        return functools.reduce(list.__add__,
                                [manager.get_subscribed_users(day) for manager in self._managers.values()])

    # TODO: REMOVE
    # TODO: This should only be a temporary thing
    # def get_users_with_no_subscriptions(self) -> 'List[User]':
    #     return functools.reduce(list.__add__,
    #                             [manager.get_users_with_no_subscriptions() for manager in self._managers.values()])

    def initialise(self):
        for manager in self._managers.values():
            manager.initialise()

    def get_identifier(self):
        return None
