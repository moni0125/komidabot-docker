import datetime

from sqlalchemy import inspect

from app import db
from komidabot.models_users import RegisteredUser, Role
from tests.base import BaseTestCase


class TestModelsRegisteredUsers(BaseTestCase):
    """
    Test models_users.RegisteredUser
    """

    def test_simple_constructors(self):
        # Test constructor of RegisteredUser model

        with self.app.app_context():
            user1 = RegisteredUser('test', '123', 'Test User 1', 'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser('test', '456', 'Test User 2', 'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser('test', '789', 'Test User 3', 'user3@example.com', 'https://example.com/img3.png')

            # Ensure that the constructor does not add the entities to the database
            self.assertTrue(inspect(user1).transient)
            self.assertTrue(inspect(user2).transient)
            self.assertTrue(inspect(user3).transient)

            db.session.add(user1)
            db.session.add(user2)
            db.session.add(user3)

            db.session.commit()

    # noinspection PyTypeChecker
    def test_invalid_constructors(self):
        # Test constructor of RegisteredUser model

        with self.app.app_context():
            with self.assertRaises(ValueError):
                RegisteredUser(None, '123', 'Test User 1', 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser(123, '123', 'Test User 1', 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', None, 'Test User 1', 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', 123, 'Test User 1', 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', None, 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', 123, 'user1@example.com', 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', 'Test User 1', None, 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', 'Test User 1', 123, 'https://example.com/img1.png')

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', 'Test User 1', 'user1@example.com', None)

            with self.assertRaises(ValueError):
                RegisteredUser('test', '123', 'Test User 1', 'user1@example.com', 123)

    def test_create(self):
        # Test usage of RegisteredUser.create

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            # Ensure that the create method adds the entities to the database
            self.assertFalse(inspect(user1).transient)
            self.assertFalse(inspect(user2).transient)
            self.assertFalse(inspect(user3).transient)

            db.session.commit()

    def test_get_by_id(self):
        # Test getting a RegisteredUser object by its internal ID

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            db.session.commit()

            self.assertEqual(user1, RegisteredUser.get_by_id(user1.id))
            self.assertEqual(user2, RegisteredUser.get_by_id(user2.id))
            self.assertEqual(user3, RegisteredUser.get_by_id(user3.id))
            self.assertEqual(None, RegisteredUser.get_by_id(user3.id + 1000))

    def test_find_by_provider_id(self):
        # Test getting a RegisteredUser object by its provider id (subject column)

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            db.session.commit()

            self.assertEqual(user1, RegisteredUser.find_by_provider_id(user1.provider, user1.subject))
            self.assertEqual(user2, RegisteredUser.find_by_provider_id(user2.provider, user2.subject))
            self.assertEqual(user3, RegisteredUser.find_by_provider_id(user3.provider, user3.subject))
            self.assertEqual(None, RegisteredUser.find_by_provider_id('Definitely not used', 'subjectId'))

    def test_find_by_email(self):
        # Test getting a RegisteredUser object by its email

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            db.session.commit()

            self.assertEqual(user1, RegisteredUser.find_by_email('user1@example.com'))
            self.assertEqual(user2, RegisteredUser.find_by_email('user2@example.com'))
            self.assertEqual(user3, RegisteredUser.find_by_email('user3@example.com'))

    def test_get_all(self):
        # Test getting all RegisteredUser objects

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            db.session.commit()

            users = RegisteredUser.get_all()
            ids = [user.id for user in users]

            self.assertEqual(len(users), 3)
            self.assertEqual(len(ids), 3)
            self.assertIn(user1.id, ids)
            self.assertIn(user2.id, ids)
            self.assertIn(user3.id, ids)

    def test_get_all_active(self):
        # Test getting all active RegisteredUser objects

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            user1.activated_on = datetime.datetime.now()
            user3.activated_on = user1.activated_on + datetime.timedelta(days=5)

            db.session.commit()

            users = RegisteredUser.get_all_active()
            ids = [user.id for user in users]

            self.assertEqual(len(users), 2)
            self.assertEqual(len(ids), 2)
            self.assertIn(user1.id, ids)
            self.assertNotIn(user2.id, ids)
            self.assertIn(user3.id, ids)

    def test_get_all_by_role(self):
        # Test getting all active RegisteredUser objects

        with self.app.app_context():
            role1 = Role.create('test_role1')
            role2 = Role.create('test_role2')

            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            user1.add_role(role1)
            user2.add_role(role1)
            user2.add_role(role2)

            db.session.commit()

            users1 = RegisteredUser.get_all_by_role(role1)
            ids1 = [user.id for user in users1]

            self.assertEqual(len(users1), 2)
            self.assertEqual(len(ids1), 2)
            self.assertIn(user1.id, ids1)
            self.assertIn(user2.id, ids1)
            self.assertNotIn(user3.id, ids1)

            users2 = RegisteredUser.get_all_by_role(role2)
            ids2 = [user.id for user in users2]

            self.assertEqual(len(users2), 1)
            self.assertEqual(len(ids2), 1)
            self.assertNotIn(user1.id, ids2)
            self.assertIn(user2.id, ids2)
            self.assertNotIn(user3.id, ids2)

    def test_roles(self):
        # Test getting all active RegisteredUser objects

        with self.app.app_context():
            role1 = Role.create('test_role1')
            role2 = Role.create('test_role2')

            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            user1.add_role(role1)
            user2.add_role(role1)
            user2.add_role(role2)

            db.session.commit()

            self.assertTrue(user1.is_role(role1))
            self.assertTrue(user2.is_role(role1))
            self.assertFalse(user3.is_role(role1))
            self.assertFalse(user1.is_role(role2))
            self.assertTrue(user2.is_role(role2))
            self.assertFalse(user3.is_role(role2))

            user2.remove_role(role1)

            self.assertTrue(user1.is_role(role1.name))
            self.assertFalse(user2.is_role(role1.name))
            self.assertFalse(user3.is_role(role1.name))
            self.assertFalse(user1.is_role(role2.name))
            self.assertTrue(user2.is_role(role2.name))
            self.assertFalse(user3.is_role(role2.name))

    def test_delete(self):
        # Test getting all RegisteredUser objects

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user3 = RegisteredUser.create('test', '789', 'Test User 3',
                                          'user3@example.com', 'https://example.com/img3.png')

            db.session.commit()

            user2.delete()

            db.session.commit()

            users = RegisteredUser.get_all()
            ids = [user.id for user in users]

            self.assertEqual(len(users), 2)
            self.assertEqual(len(ids), 2)
            self.assertIn(user1.id, ids)
            self.assertNotIn(user2.id, ids)
            self.assertIn(user3.id, ids)

    def test_user_mixin(self):
        # Test getting all RegisteredUser objects

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user2.activated_on = datetime.datetime.now()

            db.session.commit()

            self.assertIsNone(user1.activated_on)
            self.assertFalse(user1.is_active)
            self.assertTrue(user1.is_authenticated)
            self.assertFalse(user1.is_anonymous)

            self.assertIsNotNone(user2.activated_on)
            self.assertTrue(user2.is_active)
            self.assertTrue(user2.is_authenticated)
            self.assertFalse(user2.is_anonymous)

    def test_subscriptions(self):
        # Test getting all RegisteredUser objects

        with self.app.app_context():
            user1 = RegisteredUser.create('test', '123', 'Test User 1',
                                          'user1@example.com', 'https://example.com/img1.png')
            user2 = RegisteredUser.create('test', '456', 'Test User 2',
                                          'user2@example.com', 'https://example.com/img2.png')
            user1.activated_on = user2.activated_on = datetime.datetime.now()

            db.session.commit()

            # Assert that we start with no subscriptions
            self.assertEqual(len(user1.get_subscriptions()), 0)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Add a subscription to user 1
            user1.add_subscription('https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8', {'key1': 'value1'})

            # Assert adding a subscription to one user doesn't add one to another
            self.assertEqual(len(user1.get_subscriptions()), 1)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that the added subscription is the one we put in
            self.assertIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                           'keys': {'key1': 'value1'}},
                          user1.get_subscriptions())

            # Also check that we're not breaking time I guess
            self.assertNotIn({'endpoint': 'https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                              'keys': {'key2': 'value2'}},
                             user1.get_subscriptions())

            # Add a 2nd subscription to user 1
            user1.add_subscription('https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2', {'key2': 'value2'})

            # Assert adding a subscription to one user doesn't add one to another once more
            self.assertEqual(len(user1.get_subscriptions()), 2)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that all the subscriptions we added are in there
            self.assertIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                           'keys': {'key1': 'value1'}},
                          user1.get_subscriptions())
            self.assertIn({'endpoint': 'https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                           'keys': {'key2': 'value2'}},
                          user1.get_subscriptions())

            # Add the 2nd subscription to user 1 once more
            user1.add_subscription('https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2', {'key2': 'value2'})

            # Assert adding a subscription to one user doesn't add one to another once more
            self.assertEqual(len(user1.get_subscriptions()), 2)  # Length unchanged, no duplicates allowed
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that all the subscriptions we added are in there
            self.assertIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                           'keys': {'key1': 'value1'}},
                          user1.get_subscriptions())
            self.assertIn({'endpoint': 'https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                           'keys': {'key2': 'value2'}},
                          user1.get_subscriptions())

            # Try to add the 2nd subscription to user 1, but with different keys
            user1.add_subscription('https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2', {'key10': 'value10'})

            # Assert that this did not add a new subscription
            self.assertEqual(len(user1.get_subscriptions()), 2)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that the subscriptions are unchanged by this
            self.assertIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                           'keys': {'key1': 'value1'}},
                          user1.get_subscriptions())
            self.assertIn({'endpoint': 'https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                           'keys': {'key2': 'value2'}},
                          user1.get_subscriptions())

            # Try to remove the 1st subscription from user 2
            user2.remove_subscription('https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8')

            # Assert that this did nothing
            self.assertEqual(len(user1.get_subscriptions()), 2)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Remove the 1st subscription from user 1
            user1.remove_subscription('https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8')

            # Assert that this time stuff actually happened
            self.assertEqual(len(user1.get_subscriptions()), 1)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that only the subscription we removed was actually removed
            self.assertNotIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                              'keys': {'key1': 'value1'}},
                             user1.get_subscriptions())
            self.assertIn({'endpoint': 'https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                           'keys': {'key2': 'value2'}},
                          user1.get_subscriptions())

            # Bring back the 1st subscription
            user1.add_subscription('https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8', {'key1': 'value1'})

            # Replace the 2nd subscription
            user1.replace_subscription('https://example.com/2ee246b0-c8b2-4b6c-a08d-acb26ab392d2',
                                       'https://example.com/4c991903-c193-447b-ac5b-b3b8674cd5f9',
                                       {'key3': 'value3'})

            # Assert that no additional subscriptions were added, only modified
            self.assertEqual(len(user1.get_subscriptions()), 2)
            self.assertEqual(len(user2.get_subscriptions()), 0)

            # Assert that the 2nd subscription was replaced
            self.assertIn({'endpoint': 'https://example.com/6cc32b91-6938-4d8b-9f3b-f0fccc015ca8',
                           'keys': {'key1': 'value1'}},
                          user1.get_subscriptions())
            self.assertIn({'endpoint': 'https://example.com/4c991903-c193-447b-ac5b-b3b8674cd5f9',
                           'keys': {'key3': 'value3'}},
                          user1.get_subscriptions())
