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
                                            [CourseAttributes.SNACK], Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
                                            [CourseAttributes.PASTA], Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
                                            [CourseAttributes.SOUP], Decimal('1.0'), Decimal('2.0'))

            db.session.add(menu)
            db.session.commit()

            items = MenuItem.query.filter_by(menu_id=menu.id).order_by(MenuItem.id).all()

            self.assertIn(menu_item1, items)
            self.assertIn(menu_item2, items)
            self.assertIn(menu_item3, items)

    # def test_update_menu(self):
    #     # Tests updating a Menu
    #
    #     with self.app.app_context():
    #         db.session.add_all(self.campuses)
    #
    #         translatable1, _ = self.create_translation({'en': 'Translation 1: en'}, 'en', has_context=True)
    #         translatable2, _ = self.create_translation({'en': 'Translation 2: en'}, 'en', has_context=True)
    #         translatable3, _ = self.create_translation({'en': 'Translation 3: en'}, 'en', has_context=True)
    #
    #         menu1 = Menu.create(self.campuses[0], utils.DAYS['MON'])
    #
    #         db.session.flush()
    #
    #         menu_item1 = menu1.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
    #                                          [CourseAttributes.SNACK], Decimal('1.0'), None)
    #         menu_item2 = menu1.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
    #                                          [CourseAttributes.PASTA], Decimal('1.0'), Decimal('4.0'))
    #
    #         db.session.commit()
    #
    #         menu_item1_id = menu_item1.id
    #         menu_item2_id = menu_item2.id
    #
    #         menu2 = Menu.create(self.campuses[0], utils.DAYS['TUE'])
    #
    #         db.session.flush()
    #
    #         menu_item3 = menu2.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
    #                                          [CourseAttributes.SNACK], Decimal('1.0'), None)
    #         menu_item4 = menu2.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
    #                                          [CourseAttributes.SOUP], Decimal('1.0'), Decimal('2.0'))
    #
    #         db.session.commit()
    #
    #         menu_item3_id = menu_item3.id
    #         menu_item4_id = menu_item4.id
    #
    #         self.assertEqual(menu_item1, menu_item3)
    #
    #         menu1.update(menu2)
    #
    #         db.session.commit()
    #
    #         items = list(MenuItem.query.filter_by(menu_id=menu1.id).order_by(MenuItem.id).all())
    #         ids = [item.id for item in items]
    #
    #         self.assertIn(menu_item1, items)
    #         self.assertNotIn(menu_item2, items)
    #         self.assertIn(menu_item3, items)
    #         self.assertIn(menu_item4, items)
    #         self.assertEqual(len(items), 2)
    #
    #         self.assertIn(menu_item1_id, ids)
    #         self.assertNotIn(menu_item2_id, ids)
    #         self.assertNotIn(menu_item3_id, ids)
    #         self.assertNotIn(menu_item4_id, ids)
    #         self.assertEqual(len(ids), 2)

    # def test_update_menu_no_session(self):
    #     # Tests updating a Menu without adding it to the session
    #
    #     with self.app.app_context():
    #         db.session.add_all(self.campuses)
    #
    #         translatable1, _ = self.create_translation({'en': 'Translation 1: en'}, 'en', has_context=True)
    #         translatable2, _ = self.create_translation({'en': 'Translation 2: en'}, 'en', has_context=True)
    #         translatable3, _ = self.create_translation({'en': 'Translation 3: en'}, 'en', has_context=True)
    #
    #         menu1 = Menu.create(self.campuses[0], utils.DAYS['MON'])
    #
    #         db.session.flush()
    #
    #         menu_item1 = menu1.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
    #                                          [CourseAttributes.SNACK], Decimal('1.0'), None)
    #         menu_item2 = menu1.add_menu_item(translatable2, CourseType.PASTA, CourseSubType.NORMAL,
    #                                          [CourseAttributes.PASTA], Decimal('1.0'), Decimal('4.0'))
    #
    #         db.session.commit()
    #
    #         items = list(menu1.menu_items)
    #
    #         menu2 = Menu.create(self.campuses[0], utils.DAYS['TUE'], add_to_db=False)
    #
    #         menu_item3 = menu2.add_menu_item(translatable1, CourseType.SUB, CourseSubType.NORMAL,
    #                                          [CourseAttributes.SNACK], Decimal('1.0'), None)
    #         menu_item4 = menu2.add_menu_item(translatable3, CourseType.SOUP, CourseSubType.VEGAN,
    #                                          [CourseAttributes.SOUP], Decimal('1.0'), Decimal('2.0'))
    #
    #         self.assertEqual(menu_item1, menu_item3)
    #
    #         self.assertIn(menu_item1, items)
    #         self.assertIn(menu_item2, items)
    #         self.assertIn(menu_item3, items)  # Equals item1
    #         self.assertNotIn(menu_item4, items)
    #
    #         menu1.update(menu2)
    #
    #         db.session.commit()
    #
    #         items = list(menu2.menu_items)
    #
    #         self.assertIn(menu_item1, items)
    #         self.assertNotIn(menu_item2, items)
    #         self.assertIn(menu_item3, items)  # Equals item1
    #         self.assertIn(menu_item4, items)
