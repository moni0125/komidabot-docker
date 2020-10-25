from decimal import Decimal

import tests.utils as utils
from app import db
from komidabot.models import Menu, MenuItem, CourseType, CourseSubType, CourseAttributes
from tests.base import BaseTestCase


class TestModelsMenuItem(BaseTestCase):
    """
    Test models.MenuItem
    """

    def setUp(self):
        super().setUp()

        self.create_test_campuses()

    def test_simple_constructors(self):
        # Test constructor of MenuItem model

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en': 'Translation 1: en'}, 'en', has_context=True)
            translatable2, _ = self.create_translation({'en': 'Translation 2: en'}, 'en', has_context=True)
            translatable3, _ = self.create_translation({'en': 'Translation 3: en'}, 'en', has_context=True)

            menu = Menu.create(self.campuses[0], utils.DAYS['MON'])

            # Required if we need to get menu.id, otherwise it would return None
            # db.session.flush()

            # XXX: Use constructor here to test, rather than the appropriate method
            MenuItem(menu, translatable1.id, CourseType.SUB, CourseSubType.NORMAL, Decimal('1.0'), None)
            MenuItem(menu, translatable2.id, CourseType.PASTA, CourseSubType.NORMAL, Decimal('1.0'), Decimal('4.0'))
            MenuItem(menu, translatable3.id, CourseType.SOUP, CourseSubType.VEGAN, Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

    def test_add_menu_item(self):
        # Test usage of Menu.add_menu_item to check if MenuItems are constructed the same way as through their
        # constructor

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en': 'Translation 1: en'}, 'en', has_context=True)
            translatable2, _ = self.create_translation({'en': 'Translation 2: en'}, 'en', has_context=True)
            translatable3, _ = self.create_translation({'en': 'Translation 3: en'}, 'en', has_context=True)

            menu = Menu.create(self.campuses[0], utils.DAYS['MON'])

            # Required if we need to get menu.id, otherwise it would return None
            # db.session.flush()

            menu_item1 = menu.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
                                            [CourseAttributes.SNACK], Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
                                            [CourseAttributes.PASTA], Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
                                            [CourseAttributes.SOUP], Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

            self.assertEqual(len(menu.menu_items), 3)
            self.assertNotEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item2, menu_item3)
            self.assertIn(menu_item1, menu.menu_items)
            self.assertIn(menu_item2, menu.menu_items)
            self.assertIn(menu_item3, menu.menu_items)

    def test_get_translation(self):
        # Test that translation requests are passed through

        with self.app.app_context():
            trans = self.translator

            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en': 'Translation 1: en',
                                                        'nl': 'Translation 1: nl'}, 'en', has_context=True)
            translatable2, _ = self.create_translation({'en': 'Translation 2: en',
                                                        'nl': 'Translation 2: nl'}, 'en', has_context=True)
            translatable3, _ = self.create_translation({'en': 'Translation 3: en',
                                                        'nl': 'Translation 3: nl'}, 'en', has_context=True)

            menu = Menu.create(self.campuses[0], utils.DAYS['MON'])

            # Required if we need to get menu.id, otherwise it would return None
            # db.session.flush()

            menu_item1 = menu.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
                                            [CourseAttributes.SNACK], Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
                                            [CourseAttributes.PASTA], Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
                                            [CourseAttributes.SOUP], Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

            self.assertEqual(menu_item1.get_translation('en', trans), translatable1.get_translation('en', trans))
            self.assertEqual(menu_item1.get_translation('nl', trans), translatable1.get_translation('nl', trans))
            self.assertEqual(menu_item1.get_translation('fr', trans), translatable1.get_translation('fr', trans))
            self.assertEqual(menu_item2.get_translation('en', trans), translatable2.get_translation('en', trans))
            self.assertEqual(menu_item2.get_translation('nl', trans), translatable2.get_translation('nl', trans))
            self.assertEqual(menu_item2.get_translation('fr', trans), translatable2.get_translation('fr', trans))
            self.assertEqual(menu_item3.get_translation('en', trans), translatable3.get_translation('en', trans))
            self.assertEqual(menu_item3.get_translation('nl', trans), translatable3.get_translation('nl', trans))
            self.assertEqual(menu_item3.get_translation('fr', trans), translatable3.get_translation('fr', trans))
