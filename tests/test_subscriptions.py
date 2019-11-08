import datetime
import unittest
from decimal import Decimal
from typing import Dict, List, Tuple

import komidabot.triggers as triggers
import komidabot.users as users
import komidabot.models as models
import tests.users_stub as users_stub
import tests.utils as utils
from app import db
from komidabot.models import AppUser, Day, FoodType, UserSubscription, food_type_icons
from tests.base import BaseTestCase, HttpCapture, menu_item


class BaseSubscriptionsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.campuses = self.create_test_campuses()


class TestGenericSubscriptions(BaseSubscriptionsTestCase):
    def setUp(self):
        super().setUp()

        with self.app.app_context():
            user_manager = users_stub.UserManager()
            self.message_handler = user_manager.message_handler
            self.app.user_manager = user_manager  # Replace the unified user manager completely to test

            self.user1 = user_manager.add_user('user1')
            self.user2 = user_manager.add_user('user2')
            self.user3 = user_manager.add_user('user3')

            db.session.commit()

    def setup_subscriptions(self):
        def create_subscriptions(user: users.UserId, days: List[Tuple[Day, int, bool]]):
            for day, campus, active in days:
                user_obj = AppUser.find_by_id(user.provider, user.id)
                UserSubscription.create(user_obj, day, self.campuses[campus], active=active)

        with self.app.app_context():
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

            db.session.commit()

    def setup_menu(self):
        self.expected_menus = dict()  # type: Dict[Tuple[str, datetime.date], str]
        food_types = FoodType

        with self.app.app_context():
            for campus in self.campuses:
                db.session.add(campus)

                for day in utils.DAYS_LIST:
                    day_name = Day(day.isoweekday()).name
                    items = [menu_item(food_type, '{} at {} for {}'.format(food_type.name, campus.short_name, day_name),
                                       'nl_BE', Decimal('1.0'), Decimal('2.0')) for food_type in food_types]
                    TestGenericSubscriptions.create_menu(campus, day, items)

                    result = ['Menu at {} on {}'.format(campus.short_name.upper(), str(day)), '']
                    for item in items:
                        result.append('{} {} ({} / {})'.format(food_type_icons[item.type], item.text,
                                                               models.MenuItem.format_price(item.price_students),
                                                               models.MenuItem.format_price(item.price_staff)))

                    self.expected_menus[(campus.short_name, day)] = '\n'.join(result)

            db.session.commit()

    def test_active_subscriptions(self):
        self.setup_subscriptions()
        self.setup_menu()

        self.activate_feature('menu_subscription', available=True)

        with self.app.app_context():
            with HttpCapture():  # Ensure no requests are made
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['MON']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['TUE']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['WED']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['THU']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['FRI']))

                db.session.add_all(self.campuses)

                self.assertEqual(self.message_handler.message_log[self.user1.id], [
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['MON'])],
                    self.expected_menus[(self.campuses[1].short_name, utils.DAYS['TUE'])],
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['WED'])],
                    self.expected_menus[(self.campuses[1].short_name, utils.DAYS['THU'])],
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['FRI'])],
                ])

                self.assertEqual(self.message_handler.message_log[self.user2.id], [
                    self.expected_menus[(self.campuses[1].short_name, utils.DAYS['TUE'])],
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['THU'])],
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
