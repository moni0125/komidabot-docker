from typing import Dict, List

from komidabot.messages import Message
from komidabot.users import User

__all__ = ['SubscriptionChannel', 'SubscriptionManager']


class SubscriptionChannel:
    def user_supports(self, user: 'User') -> bool:
        return user.supports_subscription_channel(self.get_name()) and user.is_reachable()

    def get_subscribed_users(self, /, data=None) -> 'List[User]':
        raise NotImplementedError()

    def deliver_message(self, message: Message):
        raise NotImplementedError()

    def get_name(self) -> str:
        raise NotImplementedError()

    def user_subscribe(self, user: 'User', /, data=None) -> bool:
        raise NotImplementedError()

    def user_unsubscribe(self, user: 'User') -> bool:
        raise NotImplementedError()


class SubscriptionManager:
    def __init__(self):
        self._channels = dict()  # type: Dict[str, SubscriptionChannel]

    def register_channel(self, channel: 'SubscriptionChannel'):
        if channel.get_name() in self._channels:
            raise ValueError('Duplicate channel name registered')

        self._channels[channel.get_name()] = channel

    def get_subscribed_users(self, channel: str, /, data=None) -> 'List[User]':
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        return self._channels[channel].get_subscribed_users(data=data)

    def deliver_message(self, channel: str, message: Message):
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        return self._channels[channel].deliver_message(message)

    def user_subscribe(self, user: 'User', channel: str, /, data=None) -> bool:
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        if not channel_obj.user_supports(user):
            return False

        return channel_obj.user_subscribe(user, data=data)

    def user_unsubscribe(self, user: 'User', channel: str) -> bool:
        if channel not in self._channels:
            raise ValueError('Unknown channel')

        channel_obj = self._channels[channel]

        if not channel_obj.user_supports(user):
            return False

        return channel_obj.user_unsubscribe(user)
