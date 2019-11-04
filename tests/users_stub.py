from typing import Dict, Optional, Union

import komidabot.users as users
from komidabot.models import AppUser

PROVIDER_ID = 'stub'


class UserManager(users.UserManager):
    def __init__(self):
        self.users = dict()  # type: Dict[users.UserId,User]

        self.message_handler = None

    def add_user(self, internal_id: str) -> 'User':
        user_id = users.UserId(internal_id, PROVIDER_ID)

        if user_id in self.users:
            raise ValueError('Duplicate user ID')

        user = User(self, user_id.id)
        self.users[user_id] = user

        AppUser.create(PROVIDER_ID, internal_id, user.get_locale())

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
        db_users = AppUser.find_by_provider(PROVIDER_ID)

        for db_user in db_users:
            user_id = users.UserId(db_user.internal_id, db_user.provider)
            user = User(self, user_id.id)
            self.users[user_id] = user

    def get_identifier(self):
        return PROVIDER_ID


class User(users.User):
    def __init__(self, manager: UserManager, internal_id: str):
        self._manager = manager
        self._id = internal_id
        self._locale = 'nl_BE'

    def get_locale(self) -> 'Optional[str]':
        return self._locale

    def set_locale(self, value: str):
        self._locale = value

    def get_provider_name(self) -> 'str':
        return PROVIDER_ID

    def get_internal_id(self) -> 'str':
        return self._id

    def get_manager(self) -> UserManager:
        return self._manager

    def get_message_handler(self):
        if self._manager.message_handler is None:
            raise NotImplementedError()
        return self._manager.message_handler
