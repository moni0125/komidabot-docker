from typing import Dict, List, Optional, Union

import komidabot.messages as messages
import komidabot.models as models
import komidabot.subscriptions as subscriptions
from extensions import db
from komidabot.app import get_app
from komidabot.messages import Message
from komidabot.models import Day
from komidabot.users import User

__all__ = ['CHANNEL_ID', 'Channel']

CHANNEL_ID = 'daily_menu'


class Query(subscriptions.SubscriptionQuery):
    def __init__(self, day: models.Day, campus: models.Campus = None):
        self.day = day
        self.campus = campus


class Data(subscriptions.SubscriptionData):
    class Day:
        def __init__(self):
            self.campus = None
            self.active = False

    def __init__(self):
        self.monday = Data.Day()
        self.tuesday = Data.Day()
        self.wednesday = Data.Day()
        self.thursday = Data.Day()
        self.friday = Data.Day()

        self.days = [self.monday, self.tuesday, self.wednesday, self.thursday, self.friday]


class Channel(subscriptions.SubscriptionChannel):
    def get_subscribed_users(self, /, query: Union[Query, Dict] = None) -> 'List[User]':
        if not isinstance(query, Query):
            query = self.get_query_from(query)

        assert isinstance(query, Query), 'query must be SubscriptionQuery'

        if query.campus is not None:
            raise NotImplementedError('Cannot query by (day, campus) right now')

        app = get_app()
        user_manager = app.user_manager

        users = models.AppUser.find_subscribed_users_by_day(query.day)

        return [user for user in (user_manager.get_user(user) for user in users) if self.user_supported(user)]

    def get_query_from(self, query: Dict = None) -> Optional[Query]:
        if query is None:
            return None
        return Query(day=query.get('day'), campus=query.get('campus', None))

    def deliver_message(self, message: Message):
        if not isinstance(message, messages.SubscriptionMenuMessage):
            raise NotImplementedError('Daily menu channel only supports SubscriptionMenuMessage')

        day = Day(message.date.isoweekday())
        changed = False

        for user in self.get_subscribed_users(query=Query(day)):
            if user.send_message_or_remove(CHANNEL_ID, message):
                changed = True

        if changed:
            db.session.commit()

    def get_name(self):
        return CHANNEL_ID

    def user_subscribe(self, user: 'User', /, data: Data = None) -> bool:
        return False

    def user_unsubscribe(self, user: 'User') -> bool:
        return False

    def user_subscription_data(self, user: 'User') -> Optional[Data]:
        result = Data()
        return None  # This subscription doesn't take data
