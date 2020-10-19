import datetime
import functools
import json
from typing import Dict, List, Optional, Union
from typing import NamedTuple

import komidabot.messages as messages
import komidabot.models as models
from komidabot.app import get_app

__all__ = ['UnifiedUserManager', 'User', 'UserId', 'UserManager']


class UserId(NamedTuple):
    id: str
    provider: str

    def __repr__(self):
        return '{}/{}'.format(self.provider, self.id)


class UserManager:  # TODO: This probably could use more methods
    def get_user(self, user: 'Union[UserId, models.AppUser]', **kwargs) -> 'User':
        raise NotImplementedError()

    # def get_subscribed_users(self, day: models.Day) -> 'List[User]':
    #     warnings.warn('get_subscribed_users is deprecated', DeprecationWarning)
    #     identifier = self.get_identifier()
    #     users = models.AppUser.find_subscribed_users_by_day(day, provider=identifier)
    #
    #     return [self.get_user(UserId(user.internal_id, identifier)) for user in users]

    def get_administrators(self) -> 'List[User]':
        identifier = self.get_identifier()

        return [self.get_user(user) for user in get_app().admin_ids if user.provider == identifier]

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

    def get_is_notified_new_site(self) -> 'Optional[bool]':
        user = self.get_db_user()
        if user is None:
            return None

        return user.notified_new_site

    def set_is_notified_new_site(self, value: bool):
        user = self.get_db_user()
        if user is None:
            return

        user.notified_new_site = value

    def get_campus_for_day(self, date: Union[models.Day, datetime.date]) -> 'Optional[models.Campus]':
        user = self.get_db_user()
        if user is None:
            return None

        if isinstance(date, datetime.date):
            day = models.Day(date.isoweekday())
        elif isinstance(date, models.Day):
            day = date
        else:
            raise ValueError('date')

        return user.get_campus(day)

    def set_campus_for_day(self, campus: models.Campus, date: Union[models.Day, datetime.date]):
        user = self.get_db_user()
        if user is None:
            return

        if isinstance(date, datetime.date):
            day = models.Day(date.isoweekday())
        elif isinstance(date, models.Day):
            day = date
        else:
            raise ValueError('date')

        sub = user.get_subscription(day)

        if sub is None:
            # Make new subscription and set it to enabled by default
            user.set_campus(day, campus, True)
        else:
            user.set_campus(day, campus)

    def disable_subscription_for_day(self, date: Union[models.Day, datetime.date]) -> bool:
        user = self.get_db_user()
        if user is None:
            return False

        if isinstance(date, datetime.date):
            day = models.Day(date.isoweekday())
        elif isinstance(date, models.Day):
            day = date
        else:
            raise ValueError('date')

        sub = user.get_subscription(day)

        if sub is not None and sub.active:
            sub.active = False
            return True
        return False

    def get_subscription_for_day(self, date: Union[models.Day, datetime.date]) -> 'Optional[models.UserSubscription]':
        user = self.get_db_user()
        if user is None:
            return None

        if isinstance(date, datetime.date):
            day = models.Day(date.isoweekday())
        elif isinstance(date, models.Day):
            day = date
        else:
            raise ValueError('date')

        return user.get_subscription(day)

    def mark_reachable(self) -> bool:
        """
        Ensures the user is marked as being reachable.
        :return: True if the user was marked unreachable before, False otherwise.
        """
        user = self.get_db_user()
        if user is None:
            return False

        if not user.enabled:
            user.enabled = True
            return True

        return False

    def mark_unreachable(self):
        """
        Marks the user as being unreachable, effectively disabling subscription messages from going through.
        """
        user = self.get_db_user()
        if user is None:
            return

        user.enabled = False

    def is_reachable(self) -> bool:
        """
        Checks whether the user is reachable or not.
        :return: True if the user is reachable, False otherwise.
        """
        user = self.get_db_user()
        if user is None:
            return False

        return user.enabled

    def supports_subscription_channel(self, channel: str) -> bool:
        raise NotImplementedError()

    def delete(self):
        """
        Deletes the user from the database.
        """
        user = self.get_db_user()
        if user is None:
            return

        user.delete()

    def is_admin(self):
        user_id = self.id
        return user_id in get_app().admin_ids

    def is_feature_active(self, feature_id: str) -> bool:
        return models.Feature.is_user_participating(self.get_db_user(), feature_id)

    def get_data(self) -> Optional[Dict]:
        user = self.get_db_user()
        if user is None:
            return None

        data = user.data

        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set_data(self, data: Optional[Dict]):
        user = self.get_db_user()
        if user is None:
            return

        if data is None:
            user.data = None
        else:
            user.data = json.dumps(data)

    @property
    def manager(self) -> UserManager:
        return self.get_manager()

    def get_manager(self) -> UserManager:
        raise NotImplementedError()

    def get_message_handler(self) -> messages.MessageHandler:
        raise NotImplementedError()

    def send_message(self, message: 'messages.Message') -> 'messages.MessageSendResult':
        result = self.get_message_handler().send_message(self, message)

        app = get_app()
        if app.config.get('VERBOSE'):
            print('Sending message to user {} got result {}'.format(self.id, result),
                  flush=True)

        return result

    def send_message_or_remove(self, channel: str, message: 'messages.Message') -> bool:
        message_result = self.send_message(message)

        if message_result == messages.MessageSendResult.UNSUPPORTED:
            # Messages unsupported? Disable subscription then
            print('User {} does not support messages, removing from subscription list'.format(user.id), flush=True)

            # FIXME: For unsupported messages, we should mark the user unreachable for this specific channel instead
            self.mark_unreachable()
            return True
        if message_result == messages.MessageSendResult.UNREACHABLE:
            # Unreachable = Facebook is blocking us from sending, stop trying to send in the future
            print('User {} is unreachable, removing from subscription list'.format(user.id), flush=True)

            self.mark_unreachable()
            return True
        if message_result == messages.MessageSendResult.GONE:
            # Gone = User no longer exists, delete from database
            print('User {} is gone, removing from database'.format(user.id), flush=True)

            self.delete()
            return True

        return False

    def __repr__(self):
        user_id = self.id
        return 'User: {}'.format(user_id)


class UnifiedUserManager(UserManager):
    def __init__(self):
        self._managers = dict()  # type: Dict[str, UserManager]

    def register_manager(self, manager: UserManager):
        if manager.get_identifier() in self._managers:
            raise ValueError('Multiple managers registered for one provider')
        if isinstance(manager, UnifiedUserManager):
            raise ValueError('Cannot register the unified user manager')

        self._managers[manager.get_identifier()] = manager

    def get_user(self, user: 'Union[UserId, models.AppUser]', **kwargs) -> 'User':
        if user.provider not in self._managers:
            raise ValueError('Unknown user provider')

        return self._managers[user.provider].get_user(user, **kwargs)

    # def get_subscribed_users(self, day: models.Day):
    #     warnings.warn('get_subscribed_users is deprecated', DeprecationWarning)
    #     return functools.reduce(list.__add__,
    #                             [manager.get_subscribed_users(day) for manager in self._managers.values()])

    def get_administrators(self):
        return functools.reduce(list.__add__, [manager.get_administrators() for manager in self._managers.values()])

    def initialise(self):
        for manager in self._managers.values():
            manager.initialise()

    def get_identifier(self):
        return None
