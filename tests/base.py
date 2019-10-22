from flask.cli import ScriptInfo
from flask_testing import TestCase

from app import create_app, db


class BaseTestCase(TestCase):
    def create_app(self):
        script_info = ScriptInfo(create_app=create_app)
        script_info.data['APP_SETTINGS'] = 'config.TestingConfig'
        return script_info.load_app()

    def setUp(self):
        with self.app.app_context():
            db.create_all()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
