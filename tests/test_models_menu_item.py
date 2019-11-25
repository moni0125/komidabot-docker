import unittest
from decimal import Decimal

import komidabot.models as models
import tests.utils as utils
from app import db
from tests.base import BaseTestCase


class TestModelsMenuItem(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.create_test_campuses()

    def test_simple_constructors(self):
        # Test constructor of MenuItem model

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US'}, 'en_US', has_context=True)
            translatable3, _ = self.create_translation({'en_US': 'Translation 3: en_US'}, 'en_US', has_context=True)

            menu = models.Menu.create(self.campuses[0], utils.DAYS['MON'])

            db.session.flush()

            # XXX: Use constructor here to test, rather than the appropriate method
            models.MenuItem(menu.id, translatable1.id, models.FoodType.SUB, Decimal('1.0'), None)
            models.MenuItem(menu.id, translatable2.id, models.FoodType.PASTA_MEAT, Decimal('1.0'), Decimal('4.0'))
            models.MenuItem(menu.id, translatable3.id, models.FoodType.SOUP, Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

    def test_add_menu_item(self):
        # Test usage of Menu.add_menu_item to check if MenuItems are constructed the same way as through their
        # constructor

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US'}, 'en_US', has_context=True)
            translatable3, _ = self.create_translation({'en_US': 'Translation 3: en_US'}, 'en_US', has_context=True)

            menu = models.Menu.create(self.campuses[0], utils.DAYS['MON'])

            db.session.flush()

            menu_item1 = menu.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, models.FoodType.PASTA_MEAT, Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, models.FoodType.SOUP, Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

            self.assertEqual(len(menu.menu_items), 3)
            self.assertNotEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item2, menu_item3)
            self.assertIn(menu_item1, menu.menu_items)
            self.assertIn(menu_item2, menu.menu_items)
            self.assertIn(menu_item3, menu.menu_items)

    def test_copy(self):
        # Test the copy method of MenuItem

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)

            menu1 = models.Menu.create(self.campuses[0], utils.DAYS['MON'])
            menu2 = models.Menu.create(self.campuses[1], utils.DAYS['MON'])
            menu3 = models.Menu.create(self.campuses[2], utils.DAYS['MON'])

            db.session.flush()

            menu_item1 = menu1.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item2 = menu_item1.copy(menu2)
            menu_item3 = menu_item2.copy(menu3)

            db.session.commit()

            self.assertEqual(menu_item1, menu_item2)
            self.assertEqual(menu_item1, menu_item3)
            self.assertEqual(menu_item2, menu_item3)
            self.assertEqual(menu_item1.translatable_id, menu_item2.translatable_id)
            self.assertEqual(menu_item1.translatable_id, menu_item3.translatable_id)
            self.assertEqual(menu_item1.food_type, menu_item2.food_type)
            self.assertEqual(menu_item1.food_type, menu_item3.food_type)
            self.assertEqual(menu_item1.price_students, menu_item2.price_students)
            self.assertEqual(menu_item1.price_students, menu_item3.price_students)
            self.assertEqual(menu_item1.price_staff, menu_item2.price_staff)
            self.assertEqual(menu_item1.price_staff, menu_item3.price_staff)

    def test_equality(self):
        # Test that menu items that are the same are actually considered the same

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US'}, 'en_US', has_context=True)

            menu1 = models.Menu.create(self.campuses[0], utils.DAYS['MON'])
            menu2 = models.Menu.create(self.campuses[1], utils.DAYS['MON'])

            db.session.flush()

            menu_item1 = menu1.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item2 = menu_item1.copy(menu2)

            menu_item3 = menu1.add_menu_item(translatable2, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item4 = menu1.add_menu_item(translatable1, models.FoodType.PASTA_MEAT, Decimal('1.0'), None)
            menu_item5 = menu1.add_menu_item(translatable1, models.FoodType.SUB, Decimal('2.0'), None)
            menu_item6 = menu1.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), Decimal('2.0'))

            # db.session.add(menu1)
            # db.session.add(menu2)
            # db.session.commit()

            self.assertEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item1, menu_item4)
            self.assertNotEqual(menu_item1, menu_item5)
            self.assertNotEqual(menu_item1, menu_item6)

            # Try the other direction as well
            self.assertEqual(menu_item2, menu_item1)
            self.assertNotEqual(menu_item3, menu_item1)
            self.assertNotEqual(menu_item4, menu_item1)
            self.assertNotEqual(menu_item5, menu_item1)
            self.assertNotEqual(menu_item6, menu_item1)

            db.session.add(menu_item1)
            db.session.add(menu_item2)
            db.session.add(menu_item3)
            db.session.add(menu_item4)
            db.session.add(menu_item5)
            db.session.add(menu_item6)
            db.session.flush()

            # Check that these conditions still hold after flushing
            self.assertEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item1, menu_item4)
            self.assertNotEqual(menu_item1, menu_item5)
            self.assertNotEqual(menu_item1, menu_item6)

            # Try the other direction as well
            self.assertEqual(menu_item2, menu_item1)
            self.assertNotEqual(menu_item3, menu_item1)
            self.assertNotEqual(menu_item4, menu_item1)
            self.assertNotEqual(menu_item5, menu_item1)
            self.assertNotEqual(menu_item6, menu_item1)

            db.session.commit()

            # Check that these conditions still hold after committing
            self.assertEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item1, menu_item4)
            self.assertNotEqual(menu_item1, menu_item5)
            self.assertNotEqual(menu_item1, menu_item6)

            # Try the other direction as well
            self.assertEqual(menu_item2, menu_item1)
            self.assertNotEqual(menu_item3, menu_item1)
            self.assertNotEqual(menu_item4, menu_item1)
            self.assertNotEqual(menu_item5, menu_item1)
            self.assertNotEqual(menu_item6, menu_item1)

    def test_equality_not_added(self):
        # Test that menu items that are the same are actually considered the same

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US'}, 'en_US', has_context=True)

            menu1 = models.Menu.create(self.campuses[0], utils.DAYS['MON'])

            db.session.flush()

            menu_item1 = menu1.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), None)

            db.session.add(menu_item1)
            db.session.commit()

            menu2 = models.Menu.create(self.campuses[1], utils.DAYS['MON'])

            db.session.flush()

            menu_item2 = menu_item1.copy(menu2)
            menu_item3 = menu2.add_menu_item(translatable2, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item4 = menu2.add_menu_item(translatable1, models.FoodType.PASTA_MEAT, Decimal('1.0'), None)
            menu_item5 = menu2.add_menu_item(translatable1, models.FoodType.SUB, Decimal('2.0'), None)
            menu_item6 = menu2.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), Decimal('2.0'))

            # db.session.add(menu1)
            # db.session.add(menu2)
            # db.session.commit()

            self.assertEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item1, menu_item4)
            self.assertNotEqual(menu_item1, menu_item5)
            self.assertNotEqual(menu_item1, menu_item6)

            # Try the other direction as well
            self.assertEqual(menu_item2, menu_item1)
            self.assertNotEqual(menu_item3, menu_item1)
            self.assertNotEqual(menu_item4, menu_item1)
            self.assertNotEqual(menu_item5, menu_item1)
            self.assertNotEqual(menu_item6, menu_item1)

            db.session.add(menu_item2)
            db.session.add(menu_item3)
            db.session.add(menu_item4)
            db.session.add(menu_item5)
            db.session.add(menu_item6)
            db.session.flush()

            # Check that these conditions still hold after flushing
            self.assertEqual(menu_item1, menu_item2)
            self.assertNotEqual(menu_item1, menu_item3)
            self.assertNotEqual(menu_item1, menu_item4)
            self.assertNotEqual(menu_item1, menu_item5)
            self.assertNotEqual(menu_item1, menu_item6)

            # Try the other direction as well
            self.assertEqual(menu_item2, menu_item1)
            self.assertNotEqual(menu_item3, menu_item1)
            self.assertNotEqual(menu_item4, menu_item1)
            self.assertNotEqual(menu_item5, menu_item1)
            self.assertNotEqual(menu_item6, menu_item1)

            db.session.rollback()

    def test_get_translation(self):
        # Test that translation requests are passed through

        with self.app.app_context():
            def trans(text: str, from_language: str, to_language: str) -> str:
                return 'No translation "{}" {} -> {}'.format(text, from_language, to_language)

            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US',
                                                        'nl_BE': 'Translation 1: nl_BE'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US',
                                                        'nl_BE': 'Translation 2: nl_BE'}, 'en_US', has_context=True)
            translatable3, _ = self.create_translation({'en_US': 'Translation 3: en_US',
                                                        'nl_BE': 'Translation 3: nl_BE'}, 'en_US', has_context=True)

            menu = models.Menu.create(self.campuses[0], utils.DAYS['MON'])

            db.session.add(menu)
            db.session.flush()

            menu_item1 = menu.add_menu_item(translatable1, models.FoodType.SUB, Decimal('1.0'), None)
            menu_item2 = menu.add_menu_item(translatable2, models.FoodType.PASTA_MEAT, Decimal('1.0'), Decimal('4.0'))
            menu_item3 = menu.add_menu_item(translatable3, models.FoodType.SOUP, Decimal('1.0'), Decimal('2.0'))

            db.session.commit()

            self.assertEqual(menu_item1.get_translation('en_US', trans), translatable1.get_translation('en_US', trans))
            self.assertEqual(menu_item1.get_translation('nl_BE', trans), translatable1.get_translation('nl_BE', trans))
            self.assertEqual(menu_item1.get_translation('fr_BE', trans), translatable1.get_translation('fr_BE', trans))
            self.assertEqual(menu_item2.get_translation('en_US', trans), translatable2.get_translation('en_US', trans))
            self.assertEqual(menu_item2.get_translation('nl_BE', trans), translatable2.get_translation('nl_BE', trans))
            self.assertEqual(menu_item2.get_translation('fr_BE', trans), translatable2.get_translation('fr_BE', trans))
            self.assertEqual(menu_item3.get_translation('en_US', trans), translatable3.get_translation('en_US', trans))
            self.assertEqual(menu_item3.get_translation('nl_BE', trans), translatable3.get_translation('nl_BE', trans))
            self.assertEqual(menu_item3.get_translation('fr_BE', trans), translatable3.get_translation('fr_BE', trans))


if __name__ == '__main__':
    unittest.main()
