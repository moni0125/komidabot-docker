import datetime
from decimal import Decimal
from typing import Dict, List, Tuple

import komidabot.models as models
import komidabot.triggers as triggers
import komidabot.users as users
import komidabot.util as util
import tests.users_stub as users_stub
import tests.utils as utils
from app import db
from komidabot.models import AppUser, Day, CourseType, CourseSubType, UserDayCampusPreference, course_icons_matrix
from tests.base import BaseTestCase, HttpCapture, menu_item


class BaseSubscriptionsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.create_test_campuses()


class TestGenericSubscriptions(BaseSubscriptionsTestCase):
    def setUp(self):
        super().setUp()

        with self.app.app_context():
            user_manager = users_stub.UserManager()
            self.message_handler = user_manager.message_handler
            self.app.user_manager = user_manager  # Replace the unified user manager completely to test

            self.user1 = user_manager.add_user('user1', locale='nl')
            self.user2 = user_manager.add_user('user2', locale='nl')
            self.user3 = user_manager.add_user('user3', locale='nl')

            db.session.commit()

    def setup_subscriptions(self):
        def create_subscriptions(user: users.UserId, days: List[Tuple[Day, int, bool]]):
            for day, campus, active in days:
                user_obj = AppUser.find_by_id(user.provider, user.id)
                UserDayCampusPreference.create(user_obj, day, self.campuses[campus], active=active)

        with self.app.app_context():
            db.session.add_all(self.campuses)

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
        self.expected_menus: Dict[Tuple[str, datetime.date], str] = dict()
        course_types = CourseType
        sub_types = CourseSubType

        with self.app.app_context():
            db.session.add_all(self.campuses)

            for campus in self.campuses:
                for day in utils.DAYS_LIST:
                    day_name = Day(day.isoweekday()).name
                    items = [menu_item(course_type,
                                       sub_type,
                                       [],
                                       '{} at {} for {}'.format(course_type.name, campus.short_name, day_name),
                                       'nl',
                                       Decimal('1.0'),
                                       Decimal('2.0'))
                             for course_type in course_types
                             for sub_type in sub_types]
                    self.create_menu(campus, day, items, has_context=True)

                    result = [
                        'Menu van {date} in {campus}'.format(campus=campus.name,
                                                             date=util.date_to_string('nl', day)),
                        '',
                    ]
                    for item in items:
                        result.append('{} {} ({} / {})'.format(course_icons_matrix[item.type][item.sub_type], item.text,
                                                               models.MenuItem.format_price(item.price_students),
                                                               models.MenuItem.format_price(item.price_staff)))

                    self.expected_menus[(campus.short_name, day)] = '\n'.join(result)

            db.session.commit()

    def test_active_subscriptions(self):
        self.setup_subscriptions()
        self.setup_menu()

        with self.app.app_context():
            self.activate_feature('menu_subscription', available=True, has_context=True)

            with HttpCapture():  # Ensure no requests are made
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['MON']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['TUE']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['WED']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['THU']))
                self.app.bot.trigger_received(triggers.SubscriptionTrigger(date=utils.DAYS['FRI']))

                db.session.add_all(self.campuses)

                self.assertIn(self.user1.id, self.message_handler.message_log)
                self.assertEqual(self.message_handler.message_log[self.user1.id], [
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['MON'])],
                    self.expected_menus[(self.campuses[1].short_name, utils.DAYS['TUE'])],
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['WED'])],
                    self.expected_menus[(self.campuses[1].short_name, utils.DAYS['THU'])],
                    self.expected_menus[(self.campuses[0].short_name, utils.DAYS['FRI'])],
                ])

                self.assertIn(self.user2.id, self.message_handler.message_log)
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
