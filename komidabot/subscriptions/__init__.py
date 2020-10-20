from typing import Dict, List, Optional, Union

from komidabot.messages import Message
from komidabot.users import User

__all__ = ['SubscriptionChannel', 'SubscriptionManager']


class SubscriptionQuery:
    pass


class SubscriptionData:
    pass


class SubscriptionChannel:
    def user_supported(self, user: 'User') -> bool:
        return user.supports_subscription_channel(self.get_name()) and user.is_reachable()

    def get_subscribed_users(self, /, query: Union[SubscriptionQuery, Dict] = None) -> 'List[User]':
        raise NotImplementedError()

    def get_query_from(self, query: Dict = None) -> Optional[SubscriptionQuery]:
        raise NotImplementedError()

    def deliver_message(self, message: Message):
        raise NotImplementedError()

    def get_name(self) -> str:
        raise NotImplementedError()

    def user_subscribe(self, user: 'User', /, data: SubscriptionData = None) -> bool:
        raise NotImplementedError()

    def user_unsubscribe(self, user: 'User') -> bool:
        raise NotImplementedError()

    def user_subscription_data(self, user: 'User') -> Optional[SubscriptionData]:
        raise NotImplementedError()


class SubscriptionManager:
    def __init__(self):
        self._channels: 'Dict[str, SubscriptionChannel]' = dict()

    def register_channel(self, channel: 'SubscriptionChannel'):
        if channel.get_name() in self._channels:
            raise ValueError('Duplicate channel name registered')

        self._channels[channel.get_name()] = channel

    def get_subscribed_users(self, channel: str, /, query: Union[SubscriptionQuery, Dict] = None) -> 'List[User]':
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        return channel_obj.get_subscribed_users(query=query)

    def deliver_message(self, channel: str, message: Message):
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        return self._channels[channel].deliver_message(message)

    def user_subscribe(self, user: 'User', channel: str, /, data: SubscriptionData = None) -> bool:
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        if not channel_obj.user_supported(user):
            return False

        return channel_obj.user_subscribe(user, data=data)

    def user_unsubscribe(self, user: 'User', channel: str) -> bool:
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        if not channel_obj.user_supported(user):
            return False

        return channel_obj.user_unsubscribe(user)

    def user_subscription_data(self, user: 'User', channel: str) -> Optional[SubscriptionData]:
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        if not channel_obj.user_supported(user):
            return None

        return channel_obj.user_subscription_data(user)
