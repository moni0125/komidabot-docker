from typing import Optional

from komidabot.facebook.messages import MessageHandler as FBMessageHandler
import komidabot.messages as messages
import komidabot.users as users

import komidabot.models as models

PROVIDER_ID = 'facebook'


class UserManager(users.UserManager):
    def __init__(self):
        self.message_handler = FBMessageHandler()

    def get_user(self, user_id: users.UserId, **kwargs) -> 'User':
        if user_id.provider != PROVIDER_ID:
            raise ValueError('User id is not for Facebook')

        # TODO: This probably could use more checks or something
        # TODO: For example, check if there is a subscription
        return User(self, user_id.id)

    def get_subscribed_users(self):
        # FIXME: Use days
        return [User(self, sub.internal_id) for sub in models.AppUser.find_active(provider=PROVIDER_ID)]


class User(users.User):
    def __init__(self, manager: UserManager, id_str: str):
        self._manager = manager
        self._id = id_str

    def get_locale(self) -> 'Optional[str]':
        stored_value = super().get_locale()

        if not stored_value:
            pass  # FIXME: Use the FB API to query the user locale

        return stored_value

    def get_provider_name(self) -> 'str':
        return PROVIDER_ID

    def get_internal_id(self) -> 'str':
        return self._id

    def get_manager(self) -> UserManager:
        return self._manager

    def get_message_handler(self) -> messages.MessageHandler:
        return self._manager.message_handler
