from typing import Union

import komidabot.messages as messages
import komidabot.models as models
import komidabot.users as users
import komidabot.web.constants as web_constants
from komidabot.web.messages import MessageHandler as WebMessageHandler


class UserManager(users.UserManager):
    def __init__(self):
        self.message_handler = WebMessageHandler()

    def get_user(self, user: 'Union[users.UserId, models.AppUser]', **kwargs) -> 'User':
        if isinstance(user, models.AppUser):
            return User(self, user.internal_id)

        if user.provider != web_constants.PROVIDER_ID:
            raise ValueError('User id is not for Web')

        # TODO: This probably could use more checks or something
        #       For example: check if there is a subscription
        return User(self, user.id)

    def initialise(self):
        pass

    def get_identifier(self):
        return web_constants.PROVIDER_ID


class User(users.User):
    def __init__(self, manager: UserManager, id_str: str):
        self._manager = manager
        self._id = id_str

    def get_provider_name(self) -> 'str':
        return web_constants.PROVIDER_ID

    def get_internal_id(self) -> 'str':
        return self._id

    def get_manager(self) -> UserManager:
        return self._manager

    def get_message_handler(self) -> messages.MessageHandler:
        return self._manager.message_handler
