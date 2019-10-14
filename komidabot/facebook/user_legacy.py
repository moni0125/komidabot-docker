from abc import ABC

from flask import current_app as app

from komidabot.message_receiver import MessageReceiver
import komidabot.models as models


class User(MessageReceiver, ABC):
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._locale = None

    def send_message(self, message):
        message.recipient = self.user_id
        return app.messenger.send_message(message)

    def is_admin(self):
        return app.messenger.is_admin(self.user_id)

    def get_locale(self):
        user = models.AppUser.find_by_facebook_id(self.user_id)
        if user is not None:
            if user.language:
                return user.language
        if self._locale is None:
            self._locale = app.messenger.lookup_locale(self.user_id)
        return self._locale

    def get_id(self):
        return self.user_id
