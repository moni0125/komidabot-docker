from sqlalchemy import inspect

import komidabot.models as models
from app import db
from tests.base import BaseTestCase


class TestModelsCampus(BaseTestCase):
    def test_simple_constructors(self):
        # Test constructor of Campus model

        with self.app.app_context():
            campus1 = models.Campus('Testcampus', 'ctst')
            campus1.external_id = 0
            campus2 = models.Campus('Campus Omega', 'com')
            campus2.external_id = 0
            campus3 = models.Campus('Campus Paardenmarkt', 'cpm')
            campus3.external_id = 0

            # Ensure that the constructor does not add the entities to the database
            self.assertTrue(inspect(campus1).transient)
            self.assertTrue(inspect(campus2).transient)
            self.assertTrue(inspect(campus3).transient)

            db.session.add(campus1)
            db.session.add(campus2)
            db.session.add(campus3)

            db.session.commit()

    def test_create(self):
        # Test usage of Campus.create with add_to_db set to True

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0,
                                           add_to_db=True)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0,
                                           add_to_db=True)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0,
                                           add_to_db=True)

            # Ensure that the create method adds the entities to the database
            self.assertFalse(inspect(campus1).transient)
            self.assertFalse(inspect(campus2).transient)
            self.assertFalse(inspect(campus3).transient)

            db.session.commit()

    def test_create_no_add_to_db(self):
        # Test usage of Campus.create with add_to_db set to False

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0,
                                           add_to_db=False)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0,
                                           add_to_db=False)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0,
                                           add_to_db=False)

            # Ensure that the create method does not add the entities to the database
            self.assertTrue(inspect(campus1).transient)
            self.assertTrue(inspect(campus2).transient)
            self.assertTrue(inspect(campus3).transient)

            db.session.add(campus1)
            db.session.add(campus2)
            db.session.add(campus3)

            db.session.commit()

    # FIXME: Duplicate keywords will not be allowed in the near future
    def test_keywords(self):
        # Test keywords methods

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)

            db.session.commit()

            kw1 = campus1.get_keywords()
            kw2 = campus2.get_keywords()
            kw3 = campus3.get_keywords()

            # Campus 1
            self.assertIn('ctst', kw1)
            self.assertNotIn('com', kw1)
            self.assertNotIn('cpm', kw1)
            self.assertIn('keyword1', kw1)
            self.assertNotIn('keyword2', kw1)
            self.assertNotIn('keyword3', kw1)
            self.assertIn('shared_keyword', kw1)
            self.assertNotIn('extra_keyword', kw1)
            # Campus 2
            self.assertNotIn('ctst', kw2)
            self.assertIn('com', kw2)
            self.assertNotIn('cpm', kw2)
            self.assertNotIn('keyword1', kw2)
            self.assertIn('keyword2', kw2)
            self.assertNotIn('keyword3', kw2)
            self.assertIn('shared_keyword', kw2)
            self.assertNotIn('extra_keyword', kw2)
            # Campus 3
            self.assertNotIn('ctst', kw3)
            self.assertNotIn('com', kw3)
            self.assertIn('cpm', kw3)
            self.assertNotIn('keyword1', kw3)
            self.assertNotIn('keyword2', kw3)
            self.assertIn('keyword3', kw3)
            self.assertIn('shared_keyword', kw3)
            self.assertNotIn('extra_keyword', kw3)

            campus1.remove_keyword('keyword1')
            campus3.add_keyword('extra_keyword')

            db.session.commit()

            kw1 = campus1.get_keywords()
            kw2 = campus2.get_keywords()
            kw3 = campus3.get_keywords()

            # Campus 1
            self.assertIn('ctst', kw1)
            self.assertNotIn('com', kw1)
            self.assertNotIn('cpm', kw1)
            self.assertNotIn('keyword1', kw1)
            self.assertNotIn('keyword2', kw1)
            self.assertNotIn('keyword3', kw1)
            self.assertIn('shared_keyword', kw1)
            self.assertNotIn('extra_keyword', kw1)
            # Campus 2
            self.assertNotIn('ctst', kw2)
            self.assertIn('com', kw2)
            self.assertNotIn('cpm', kw2)
            self.assertNotIn('keyword1', kw2)
            self.assertIn('keyword2', kw2)
            self.assertNotIn('keyword3', kw2)
            self.assertIn('shared_keyword', kw2)
            self.assertNotIn('extra_keyword', kw2)
            # Campus 3
            self.assertNotIn('ctst', kw3)
            self.assertNotIn('com', kw3)
            self.assertIn('cpm', kw3)
            self.assertNotIn('keyword1', kw3)
            self.assertNotIn('keyword2', kw3)
            self.assertIn('keyword3', kw3)
            self.assertIn('shared_keyword', kw3)
            self.assertIn('extra_keyword', kw3)

    def test_get_by_id(self):
        # Test getting a Campus object by its ID

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)

            db.session.commit()

            self.assertEqual(campus1, models.Campus.get_by_id(campus1.id))
            self.assertEqual(campus2, models.Campus.get_by_id(campus2.id))
            self.assertEqual(campus3, models.Campus.get_by_id(campus3.id))

    def test_get_by_short_name(self):
        # Test getting a Campus object by its short name

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)

            db.session.commit()

            self.assertEqual(campus1, models.Campus.get_by_short_name('ctst'))
            self.assertEqual(campus2, models.Campus.get_by_short_name('com'))
            self.assertEqual(campus3, models.Campus.get_by_short_name('cpm'))

    # FIXME: Duplicate keywords will not be allowed in the near future -> Results will be Optional[Campus]
    def test_find_by_keyword(self):
        # Test getting campuses by a keyword

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)
            campus3.active = False

            db.session.commit()

            self.assertEqual(models.Campus.find_by_keyword('ctst'), [campus1])
            self.assertEqual(models.Campus.find_by_keyword('com'), [campus2])
            self.assertEqual(models.Campus.find_by_keyword('cpm'), [campus3])
            self.assertEqual(models.Campus.find_by_keyword('keyword1'), [campus1])
            self.assertEqual(models.Campus.find_by_keyword('keyword2'), [campus2])
            self.assertEqual(models.Campus.find_by_keyword('keyword3'), [campus3])

            campuses = models.Campus.find_by_keyword('shared_keyword')
            ids = [campus.id for campus in campuses]

            self.assertEqual(len(campuses), 3)
            self.assertEqual(len(ids), 3)
            self.assertIn(campus1.id, ids)
            self.assertIn(campus2.id, ids)
            self.assertIn(campus3.id, ids)

    def test_get_all(self):
        # Test getting all campuses

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)
            campus3.active = False

            db.session.commit()

            campuses = models.Campus.get_all()
            ids = [campus.id for campus in campuses]

            self.assertEqual(len(campuses), 3)
            self.assertEqual(len(ids), 3)
            self.assertIn(campus1.id, ids)
            self.assertIn(campus2.id, ids)
            self.assertIn(campus3.id, ids)

    def test_get_all_active(self):
        # Test getting all campuses marked as active

        with self.app.app_context():
            campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
            campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
            campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)
            campus3.active = False

            db.session.commit()

            campuses = models.Campus.get_all_active()
            ids = [campus.id for campus in campuses]

            self.assertEqual(len(campuses), 2)
            self.assertEqual(len(ids), 2)
            self.assertIn(campus1.id, ids)
            self.assertIn(campus2.id, ids)
            self.assertNotIn(campus3.id, ids)
