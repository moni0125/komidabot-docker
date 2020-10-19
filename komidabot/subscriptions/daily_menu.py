from typing import List

import komidabot.messages as messages
import komidabot.models as models
from extensions import db
from komidabot.app import get_app
from komidabot.messages import Message
from komidabot.models import Day
from komidabot.subscriptions import SubscriptionChannel
from komidabot.users import User

__all__ = ['CHANNEL_ID', 'Channel']

CHANNEL_ID = 'daily_menu'


class Channel(SubscriptionChannel):
    def get_subscribed_users(self, /, data=None) -> 'List[User]':
        # day: models.Day = None, campus: models.Campus = None
        if data is None:
            raise ValueError('Missing data')
        if 'day' not in data:
            raise ValueError('Missing day in data')
        if 'campus' in data:
            raise NotImplementedError('Cannot query by (day, campus) right now')

        day = data['day']
        if not isinstance(day, models.Day):
            raise ValueError('Day should be of type models.Day')

        app = get_app()
        user_manager = app.user_manager

        users = models.AppUser.find_subscribed_users_by_day(day)

        return [user for user in (user_manager.get_user(user) for user in users) if self.user_supports(user)]

    def deliver_message(self, message: Message):
        if not isinstance(message, messages.SubscriptionMenuMessage):
            raise NotImplementedError('Daily menu channel only supports SubscriptionMenuMessage')

        day = Day(message.date.isoweekday())
        changed = False

        for user in self.get_subscribed_users(data={'day': day}):
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
