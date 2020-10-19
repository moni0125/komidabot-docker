from typing import List

import komidabot.messages as messages
from extensions import db
from komidabot.app import get_app
from komidabot.subscriptions import SubscriptionChannel
from komidabot.users import User

__all__ = ['CHANNEL_ID', 'Channel']

CHANNEL_ID = 'administration'


class Channel(SubscriptionChannel):
    # noinspection PyMethodOverriding
    def get_subscribed_users(self, /, data=None) -> 'List[User]':
        app = get_app()
        user_manager = app.user_manager

        return [user for user in user_manager.get_administrators() if self.user_supports(user)]

    def deliver_message(self, message: messages.Message):
        changed = False

        for user in self.get_subscribed_users():
            if user.send_message_or_remove(CHANNEL_ID, message):
                changed = True

        if changed:
            db.session.commit()

    def get_name(self):
        return CHANNEL_ID

    def user_subscribe(self, user: 'User', /, data=None) -> bool:
        return False

    def user_unsubscribe(self, user: 'User') -> bool:
        return False
