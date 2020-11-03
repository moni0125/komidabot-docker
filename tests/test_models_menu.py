from decimal import Decimal

import tests.utils as utils
from app import db
from komidabot.models import Menu, MenuItem, CourseType, CourseSubType, CourseAttributes
from tests.base import BaseTestCase


class TestModelsMenu(BaseTestCase):
    """
    Test models.Menu
    """

    def setUp(self):
        super().setUp()

        self.create_test_campuses()

    def test_simple_constructors(self):
        # Test constructor of Menu model

        with self.app.app_context():
            db.session.add_all(self.campuses)

            # XXX: Use constructor here to test, rather than the appropriate method
            menu1 = Menu(self.campuses[0].id, utils.DAYS['MON'])
            menu2 = Menu(self.campuses[1].id, utils.DAYS['TUE'])
            menu3 = Menu(self.campuses[0].id, utils.DAYS['WED'])
            menu4 = Menu(self.campuses[1].id, utils.DAYS['THU'])
            menu5 = Menu(self.campuses[0].id, utils.DAYS['FRI'])

            db.session.add(menu1)
            db.session.add(menu2)
            db.session.add(menu3)
            db.session.add(menu4)
            db.session.add(menu5)
            db.session.commit()

    # noinspection PyTypeChecker
    def test_invalid_constructors(self):
        # Test constructor of Campus model

        with self.app.app_context():
            db.session.add_all(self.campuses)

            with self.assertRaises(ValueError):
                Menu(None, utils.DAYS['MON'])

            with self.assertRaises(ValueError):
                Menu('id', utils.DAYS['MON'])

            with self.assertRaises(ValueError):
                Menu(self.campuses[0].id, None)

            with self.assertRaises(ValueError):
                Menu(self.campuses[0].id, '2020-02-20')

    def test_create(self):
        # Test usage of Menu.create to check if Menus are constructed the same way as through their constructor

        with self.app.app_context():
            db.session.add_all(self.campuses)

            Menu.create(self.campuses[0], utils.DAYS['MON'])
            Menu.create(self.campuses[1], utils.DAYS['TUE'])
            Menu.create(self.campuses[0], utils.DAYS['WED'])
            Menu.create(self.campuses[1], utils.DAYS['THU'])
            Menu.create(self.campuses[0], utils.DAYS['FRI'])

            db.session.commit()

    def test_create_no_add_first(self):
        # Tests usage of Menu.create with add_to_db=False, and manually adding it afterwards

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en': 'Translation 1: en'}, 'en', has_context=True)
            translatable2, _ = self.create_translation({'en': 'Translation 2: en'}, 'en', has_context=True)
            translatable3, _ = self.create_translation({'en': 'Translation 3: en'}, 'en', has_context=True)

            menu = Menu.create(self.campuses[0], utils.DAYS['MON'], add_to_db=False)

            menu_item1 = menu.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
                                            [CourseAttributes.SNACK], [], Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
                                            [CourseAttributes.PASTA], [], Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
                                            [CourseAttributes.SOUP], [], Decimal('1.0'), Decimal('2.0'))

            db.session.add(menu)
            db.session.commit()

            items = MenuItem.query.filter_by(menu_id=menu.id).order_by(MenuItem.id).all()

            self.assertIn(menu_item1, items)
            self.assertIn(menu_item2, items)
            self.assertIn(menu_item3, items)
