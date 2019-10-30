import datetime, unittest, requests
from typing import Dict, List, Tuple

from komidabot.app import get_app
import komidabot.messages as messages
from komidabot.models import AppUser, Day, FoodType, UserSubscription, food_type_icons
import komidabot.triggers as triggers

from app import db

from tests.base import BaseTestCase, HttpCapture, menu_item
from tests.users_stub import UserManager as TestUserManager, users, PROVIDER_ID


class BaseSubscriptionsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.campuses = self.create_test_campuses()


class TestMessageHandler(messages.MessageHandler):
    def __init__(self):
        self.message_log = dict()  # type: Dict[users.UserId, List[str]]

    def reset(self):
        self.message_log = dict()

    def send_message(self, user, message: 'messages.Message'):
        if user.id.provider != PROVIDER_ID:
            raise ValueError('User id is not for Facebook')

        if isinstance(message, messages.TextMessage):
            if user.id not in self.message_log:
                self.message_log[user.id] = []
            self.message_log[user.id].append(message.text)
        else:
            raise NotImplementedError()


class TestGenericSubscriptions(BaseSubscriptionsTestCase):
    def setUp(self):
        super().setUp()

        self.day_mon = datetime.date(2019, 7, 1)
        self.day_tue = datetime.date(2019, 7, 2)
        self.day_wed = datetime.date(2019, 7, 3)
        self.day_thu = datetime.date(2019, 7, 4)
        self.day_fri = datetime.date(2019, 7, 5)

        self.days = [self.day_mon, self.day_tue, self.day_wed, self.day_thu, self.day_fri]

        with self.app.app_context():
            app = get_app()
            user_manager = TestUserManager()
            self.message_handler = user_manager.message_handler = TestMessageHandler()
            app.user_manager = user_manager  # Replace the unified user manager completely to test

            self.user1 = user_manager.add_user('user1')
            self.user2 = user_manager.add_user('user2')
            self.user3 = user_manager.add_user('user3')

    def setup_subscriptions(self):
        def create_subscriptions(user: users.UserId, days: List[Tuple[Day, int, bool]]):
            for day, campus, active in days:
                user_obj = AppUser.find_by_id(user.provider, user.id)
                UserSubscription.create(user_obj, day, self.campuses[campus], active=active, session=session)

        with self.app.app_context():
            session = db.session  # FIXME: Create new session?

            # First user, subscribed every day
            create_subscriptions(self.user1.id, [
                (Day.MONDAY, 0, True),
                (Day.TUESDAY, 1, True),
                (Day.WEDNESDAY, 0, True),
                (Day.THURSDAY, 1, True),
                (Day.FRIDAY, 0, True),
            ])

            # Second user, always goes on tuesdays and thursdays, otherwise sporadically
            create_subscriptions(self.user2.id, [
                (Day.MONDAY, 1, False),
                (Day.TUESDAY, 1, True),
                (Day.WEDNESDAY, 1, False),
                (Day.THURSDAY, 0, True),
                (Day.FRIDAY, 0, False),
            ])

            # Third user, only comes when he wants to
            create_subscriptions(self.user3.id, [
                (Day.MONDAY, 0, False),
                (Day.TUESDAY, 0, False),
                (Day.WEDNESDAY, 1, False),
                (Day.THURSDAY, 1, False),
                (Day.FRIDAY, 1, False),
            ])

            session.commit()

    def setup_menu(self):
        self.expected_menus = dict()  # type: Dict[Tuple[str, datetime.date], str]
        food_types = FoodType

        with self.app.app_context():
            session = db.session  # FIXME: Create new session?

            for campus in self.campuses:
                session.add(campus)

                for day in self.days:
                    day_name = Day(day.isoweekday()).name
                    items = [menu_item(food_type, '{} at {} for {}'.format(food_type.name, campus.short_name, day_name),
                                       'nl_BE', '€0,00', '€0,00') for food_type in food_types]
                    self.create_menu(campus, day, items, session=session)

                    result = ['Menu at {} on {}'.format(campus.short_name.upper(), str(day)), '']
                    for item in items:
                        result.append('{} {} ({} / {})'.format(food_type_icons[item.type], item.text,
                                                               item.price_students, item.price_staff))

                    self.expected_menus[(campus.short_name, day)] = '\n'.join(result)

            session.commit()

    def test_setup(self):
        self.assertEqual(self.day_mon.isoweekday(), 1, 'Date is not a Monday')
        self.assertEqual(self.day_tue.isoweekday(), 2, 'Date is not a Tuesday')
        self.assertEqual(self.day_wed.isoweekday(), 3, 'Date is not a Wednesday')
        self.assertEqual(self.day_thu.isoweekday(), 4, 'Date is not a Thursday')
        self.assertEqual(self.day_fri.isoweekday(), 5, 'Date is not a Friday')

    def test_active_subscriptions(self):
        self.setup_subscriptions()
        self.setup_menu()

        self.activate_feature('menu_subscription', available=True)

        with self.app.app_context():
            self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=self.day_mon))
            self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=self.day_tue))
            self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=self.day_wed))
            self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=self.day_thu))
            self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=self.day_fri))

            db.session.add_all(self.campuses)

            self.assertEqual(self.message_handler.message_log[self.user1.id], [
                self.expected_menus[(self.campuses[0].short_name, self.day_mon)],
                self.expected_menus[(self.campuses[1].short_name, self.day_tue)],
                self.expected_menus[(self.campuses[0].short_name, self.day_wed)],
                self.expected_menus[(self.campuses[1].short_name, self.day_thu)],
                self.expected_menus[(self.campuses[0].short_name, self.day_fri)],
            ])

            self.assertEqual(self.message_handler.message_log[self.user2.id], [
                self.expected_menus[(self.campuses[1].short_name, self.day_tue)],
                self.expected_menus[(self.campuses[0].short_name, self.day_thu)],
            ])

            self.assertNotIn(self.user3.id, self.message_handler.message_log)

            # print(self.message_handler.message_log, flush=True)


# class TestFacebookSubscriptions(BaseSubscriptionsTestCase):
#     def test_http_capture(self):
#         with self.app.app_context():
#             with HttpCapture() as http:
#                 http.register_uri(HttpCapture.GET, 'https://google.be', 'test')
#
#                 response = requests.get('https://google.be')
#
#                 assert response.text == 'test'


if __name__ == '__main__':
    unittest.main()
