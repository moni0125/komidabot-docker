from sqlalchemy import inspect

import komidabot.models as models
from app import db
from tests.base import BaseTestCase


# TODO: Add provider tests
class TestModelsTranslations(BaseTestCase):
    """
    Test models.Translatable and models.Translation
    """

    def test_simple_constructors(self):
        # Test constructor of Translatable and Translation models

        with self.app.app_context():
            translatable1 = models.Translatable('Translation 1: en', 'en')
            translatable2 = models.Translatable('Translation 2: en', 'en')
            translatable3 = models.Translatable('Translation 3: en', 'en')

            # Ensure that the constructor does not add the entities to the database
            self.assertTrue(inspect(translatable1).transient)
            self.assertTrue(inspect(translatable2).transient)
            self.assertTrue(inspect(translatable3).transient)

            db.session.add(translatable1)
            db.session.add(translatable2)
            db.session.add(translatable3)

            db.session.flush()

            translation1a = models.Translation(translatable1.id, 'nl', 'Translation 1: nl')
            translation1b = models.Translation(translatable1.id, 'fr', 'Translation 1: fr')

            self.assertTrue(inspect(translation1a).transient)
            self.assertTrue(inspect(translation1b).transient)

            db.session.add(translatable1)
            db.session.add(translatable2)

            db.session.commit()

            translation2 = models.Translation(translatable2.id, 'nl', 'Translation 2: nl')

            self.assertTrue(inspect(translation2).transient)

            db.session.add(translation2)

            db.session.commit()

    def test_get_or_create(self):
        # Test usage of Translatable.get_or_create

        with self.app.app_context():
            translatable1, translation1 = models.Translatable.get_or_create('Translation 1: en', 'en')
            translatable2, translation2 = models.Translatable.get_or_create('Translation 2: en', 'en')
            translatable3, translation3 = models.Translatable.get_or_create('Translation 3: en', 'en')

            # Ensure that the create method adds the entities to the database
            self.assertFalse(inspect(translatable1).transient)
            self.assertFalse(inspect(translation1).transient)
            self.assertFalse(inspect(translatable2).transient)
            self.assertFalse(inspect(translation2).transient)
            self.assertFalse(inspect(translatable3).transient)
            self.assertFalse(inspect(translation3).transient)

            db.session.commit()

    def test_add_translation(self):
        # Test usage of Translatable.add_translation

        with self.app.app_context():
            translatable1, translation1a = models.Translatable.get_or_create('Translation 1: en', 'en')
            translatable2, translation2a = models.Translatable.get_or_create('Translation 2: en', 'en')
            translatable3, translation3a = models.Translatable.get_or_create('Translation 3: en', 'en')

            translation1b = translatable1.add_translation('nl', 'Translation 1: nl')

            db.session.flush()

            translation2b = translatable2.add_translation('nl', 'Translation 2: nl')

            db.session.commit()

            translation3b = translatable3.add_translation('nl', 'Translation 3: nl')

            db.session.commit()

            translations1 = translatable1.translations
            translations2 = translatable2.translations
            translations3 = translatable3.translations

            self.assertEqual(len(translations1), 2)
            self.assertEqual(len(translations2), 2)
            self.assertEqual(len(translations3), 2)
            self.assertIn(translation1a, translations1)
            self.assertIn(translation1b, translations1)
            self.assertIn(translation2a, translations2)
            self.assertIn(translation2b, translations2)
            self.assertIn(translation3a, translations3)
            self.assertIn(translation3b, translations3)

    def test_has_translation(self):
        # Test usage of Translatable.add_translation

        with self.app.app_context():
            translatable1, translation1a = models.Translatable.get_or_create('Translation 1: en', 'en')
            translatable2, translation2a = models.Translatable.get_or_create('Translation 2: nl', 'nl')

            translatable1.add_translation('nl', 'Translation 1: nl')

            db.session.flush()

            translatable2.add_translation('en', 'Translation 2: en')

            db.session.commit()

            self.assertTrue(translatable1.has_translation('en'))
            self.assertTrue(translatable2.has_translation('en'))
            self.assertTrue(translatable1.has_translation('nl'))
            self.assertTrue(translatable2.has_translation('nl'))
            self.assertFalse(translatable1.has_translation('fr'))
            self.assertFalse(translatable2.has_translation('fr'))

    # TODO: Test get_translation
    def test_get_translation(self):
        # Test usage of Translatable.get_translation

        with self.app.app_context():
            translatable1, translation1a = models.Translatable.get_or_create('Translation 1: en', 'en')
            translatable2, translation2a = models.Translatable.get_or_create('Translation 2: en', 'en')
            translatable3, translation3a = models.Translatable.get_or_create('Translation 3: en', 'en')

            translation1b = translatable1.add_translation('nl', 'Translation 1: nl')
            translation2b = translatable2.add_translation('nl', 'Translation 2: nl')
            translation3b = translatable3.add_translation('nl', 'Translation 3: nl')

            db.session.commit()

            self.assertEqual(translatable1.get_translation('en', None), translation1a)
            self.assertEqual(translatable2.get_translation('en', None), translation2a)
            self.assertEqual(translatable3.get_translation('en', None), translation3a)
            self.assertEqual(translatable1.get_translation('nl', None), translation1b)
            self.assertEqual(translatable2.get_translation('nl', None), translation2b)
            self.assertEqual(translatable3.get_translation('nl', None), translation3b)

            translation1c = translatable1.get_translation('fr', self.translator)
            translation2c = translatable2.get_translation('fr', self.translator)
            translation3c = translatable3.get_translation('fr', self.translator)

            db.session.commit()

            self.assertNotEqual(translation1c, translation1a)
            self.assertNotEqual(translation1c, translation1b)
            self.assertNotEqual(translation2c, translation2a)
            self.assertNotEqual(translation2c, translation2b)
            self.assertNotEqual(translation3c, translation3a)
            self.assertNotEqual(translation3c, translation3b)

            for translation in [translation1c, translation2c, translation3c]:
                translatable: models.Translatable = translation.translatable

                self.assertEqual(translation.translation, self.translator.translate(translatable.original_text,
                                                                                    translatable.original_language,
                                                                                    translation.language))

    def test_get_by_id(self):
        # Test usage of Translatable.get_by_id

        with self.app.app_context():
            translatable1, _ = models.Translatable.get_or_create('Translation 1: en', 'en')
            translatable2, _ = models.Translatable.get_or_create('Translation 2: en', 'en')
            translatable3, _ = models.Translatable.get_or_create('Translation 3: en', 'en')

            db.session.commit()

            self.assertEqual(translatable1, models.Translatable.get_by_id(translatable1.id))
            self.assertEqual(translatable2, models.Translatable.get_by_id(translatable2.id))
            self.assertEqual(translatable3, models.Translatable.get_by_id(translatable3.id))
