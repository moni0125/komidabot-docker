from typing import Dict, List, Optional, Union

import komidabot.messages as messages
import komidabot.subscriptions as subscriptions
from extensions import db
from komidabot.app import get_app
from komidabot.users import User

__all__ = ['CHANNEL_ID', 'Channel']

CHANNEL_ID = 'administration'


class Query(subscriptions.SubscriptionQuery):
    pass


class Data(subscriptions.SubscriptionData):
    pass


class Channel(subscriptions.SubscriptionChannel):
    # noinspection PyMethodOverriding
    def get_subscribed_users(self, /, query: Union[Query, Dict] = None) -> 'List[User]':
        if not isinstance(query, Query):
            query = self.get_query_from(query)

        assert query is None or isinstance(query, Query), 'query must be None or SubscriptionQuery'

        app = get_app()
        user_manager = app.user_manager

        return [user for user in user_manager.get_administrators() if self.user_supported(user)]

    def get_query_from(self, query: Dict = None) -> Optional:
        if query is None:
            return None
        return Query()

    def deliver_message(self, message: messages.Message):
        changed = False

        for user in self.get_subscribed_users(query=Query()):
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
        return None  # This subscription doesn't take data
