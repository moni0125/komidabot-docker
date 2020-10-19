import unittest

from sqlalchemy import inspect

import komidabot.models as models
import tests.utils as utils
from app import db
from tests.base import BaseTestCase


class TestModelsClosingDays(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.create_test_campuses()

    def test_simple_constructors(self):
        # Test constructor of ClosingDays model

        with self.app.app_context():
            db.session.add_all(self.campuses)

            translatable1, _ = self.create_translation({'en_US': 'Translation 1: en_US'}, 'en_US', has_context=True)
            translatable2, _ = self.create_translation({'en_US': 'Translation 2: en_US'}, 'en_US', has_context=True)
            translatable3, _ = self.create_translation({'en_US': 'Translation 3: en_US'}, 'en_US', has_context=True)

            closed1 = models.ClosingDays(self.campuses[0].id, utils.DAYS['MON'], utils.DAYS['MON'], translatable1.id)
            closed2 = models.ClosingDays(self.campuses[1].id, utils.DAYS['TUE'], utils.DAYS['FRI'], translatable2.id)
            closed3 = models.ClosingDays(self.campuses[2].id, utils.DAYS['THU'], utils.DAYS['THU'], translatable3.id)

            # Ensure that the constructor does not add the entities to the database
            self.assertTrue(inspect(closed1).transient)
            self.assertTrue(inspect(closed2).transient)
            self.assertTrue(inspect(closed3).transient)

            db.session.add(closed1)
            db.session.add(closed2)
            db.session.add(closed3)

            db.session.commit()

    def test_create(self):
        # Test usage of ClosingDays.create with add_to_db set to True

        with self.app.app_context():
            db.session.add_all(self.campuses)

            closed1 = models.ClosingDays.create(self.campuses[0], utils.DAYS['MON'], utils.DAYS['MON'],
                                                'Translation 1: en_US', 'en_US', add_to_db=True)
            closed2 = models.ClosingDays.create(self.campuses[1], utils.DAYS['TUE'], utils.DAYS['FRI'],
                                                'Translation 2: en_US', 'en_US', add_to_db=True)
            closed3 = models.ClosingDays.create(self.campuses[2], utils.DAYS['THU'], utils.DAYS['THU'],
                                                'Translation 3: en_US', 'en_US', add_to_db=True)

            # Ensure that the create method adds the entities to the database
            self.assertFalse(inspect(closed1).transient)
            self.assertFalse(inspect(closed2).transient)
            self.assertFalse(inspect(closed3).transient)

            db.session.commit()

    def test_create_no_add_to_db(self):
        # Test usage of Campus.create with add_to_db set to False

        with self.app.app_context():
            db.session.add_all(self.campuses)

            closed1 = models.ClosingDays.create(self.campuses[0], utils.DAYS['MON'], utils.DAYS['MON'],
                                                'Translation 1: en_US', 'en_US', add_to_db=False)
            closed2 = models.ClosingDays.create(self.campuses[1], utils.DAYS['TUE'], utils.DAYS['FRI'],
                                                'Translation 2: en_US', 'en_US', add_to_db=False)
            closed3 = models.ClosingDays.create(self.campuses[2], utils.DAYS['THU'], utils.DAYS['THU'],
                                                'Translation 3: en_US', 'en_US', add_to_db=False)

            # Ensure that the create method does not add the entities to the database
            self.assertTrue(inspect(closed1).transient)
            self.assertTrue(inspect(closed2).transient)
            self.assertTrue(inspect(closed3).transient)

            db.session.add(closed1)
            db.session.add(closed2)
            db.session.add(closed3)

            db.session.commit()

    def test_find_is_closed(self):
        # Test finding if a campus is closed on a specific day

        with self.app.app_context():
            db.session.add_all(self.campuses)

            closed1 = models.ClosingDays.create(self.campuses[0], utils.DAYS['TUE'], utils.DAYS['TUE'],
                                                'Translation 1: en_US', 'en_US')
            closed2 = models.ClosingDays.create(self.campuses[1], utils.DAYS['TUE'], utils.DAYS['THU'],
                                                'Translation 2: en_US', 'en_US')
            closed3 = models.ClosingDays.create(self.campuses[2], utils.DAYS['WED'], None,
                                                'Translation 3: en_US', 'en_US')

            db.session.commit()

            # Campus 1
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[0], utils.DAYS['MON']))
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[0], utils.DAYS['TUE']), closed1)
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[0], utils.DAYS['WED']))
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[0], utils.DAYS['THU']))
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[0], utils.DAYS['FRI']))
            # Campus 2
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[1], utils.DAYS['MON']))
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[1], utils.DAYS['TUE']), closed2)
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[1], utils.DAYS['WED']), closed2)
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[1], utils.DAYS['THU']), closed2)
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[1], utils.DAYS['FRI']))
            # Campus 3
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[2], utils.DAYS['MON']))
            self.assertIsNone(models.ClosingDays.find_is_closed(self.campuses[2], utils.DAYS['TUE']))
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[2], utils.DAYS['WED']), closed3)
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[2], utils.DAYS['THU']), closed3)
            self.assertEqual(models.ClosingDays.find_is_closed(self.campuses[2], utils.DAYS['FRI']), closed3)
