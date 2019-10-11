import datetime

from komidabot.facebook.messages import MessageHandler as FBMessageHandler
import komidabot.users as users

from komidabot.models import Campus, Day, Subscription


class UserManager(users.UserManager):
    MANAGER_ID = 'facebook'

    def __init__(self):
        self.message_handler = FBMessageHandler()

    def get_user(self, user_id: users.UserId, **kwargs) -> 'User':
        if user_id.provider != UserManager.MANAGER_ID:
            raise ValueError('User id is not for Facebook')

        # TODO: This probably could use more checks or something
        # TODO: For example, check if there is a subscription
        return User(self, user_id.id)

    def get_subscribed_users(self):
        return Subscription.find_active(provider=UserManager.MANAGER_ID)

    def get_message_handler(self, user: users.User):
        if not isinstance(user, User):
            raise ValueError('User is from wrong UserManager')

        return self.message_handler  # TODO: Figure out if this needs to be per person or for multicasting purposes


class User(users.User):
    def __init__(self, manager: UserManager, id_str: str):
        self._manager = manager
        self._id = id_str

    def get_locale(self):
        # FIXME
        subscription = Subscription.find_by_facebook_id(self._id)

        return subscription.language

    def get_campus_for_day(self, date: datetime.date) -> Campus:
        day = Day(date.isoweekday())
        # FIXME
        subscription = Subscription.find_by_facebook_id(self._id)

        return subscription.get_campus(day)

    @property
    def id(self) -> users.UserId:
        return users.UserId(self._id, UserManager.MANAGER_ID)

    @property
    def manager(self) -> UserManager:
        return self._manager
