import tests.users_stub as users_stub
from app import db
from komidabot.subscriptions.administration import CHANNEL_ID as ADMINISTRATION_ID
from komidabot.users import UserId
from tests.base import BaseTestCase


class TestUsersBase(BaseTestCase):
    """
    Tests subscription channel "administration".

    Note that this (currently) relies on the stub users indicating they support this channel.
    """

    def setUp(self):
        super().setUp()

        with self.app.app_context():
            user_manager = users_stub.UserManager()
            self.message_handler = user_manager.message_handler
            self.app.user_manager.register_manager(user_manager)

            self.app.admin_ids = [UserId('admin1', users_stub.PROVIDER_ID), UserId('admin2', users_stub.PROVIDER_ID)]

            self.user1 = user_manager.add_user('user1', locale='nl')
            self.user2 = user_manager.add_user('user2', locale='nl')

            # Defined in TestingConfig
            self.admin1 = user_manager.add_user('admin1', locale='nl')
            self.admin2 = user_manager.add_user('admin2', locale='nl')

            db.session.commit()

    def test_get_subscribed_users(self):
        with self.app.app_context():
            administrators = self.app.subscription_manager.get_subscribed_users(ADMINISTRATION_ID)

            self.assertEqual(len(administrators), 2)
            self.assertNotIn(self.user1, administrators)
            self.assertNotIn(self.user2, administrators)
            self.assertIn(self.admin1, administrators)
            self.assertIn(self.admin2, administrators)
