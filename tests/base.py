import datetime
from decimal import Decimal
from typing import List, NamedTuple

import httpretty
from flask.cli import ScriptInfo
from flask_testing import TestCase

import komidabot.users as users
from app import create_app, db
from komidabot.app import App
from komidabot.models import AppUser, Campus, Feature, FoodType, Menu, Translatable

menu_item = NamedTuple('menu_item', [('type', FoodType),
                                     ('text', str),
                                     ('language', str),
                                     ('price_students', Decimal),
                                     ('price_staff', Decimal)])


class BaseTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # noinspection PyTypeChecker
        self.app = None  # type: App

    def create_app(self):
        script_info = ScriptInfo(create_app=create_app)
        script_info.data['APP_SETTINGS'] = 'config.TestingConfig'
        return script_info.load_app()

    def setUp(self):
        super().setUp()

        with self.app.app_context():
            db.create_all()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

        super().tearDown()

    def create_test_campuses(self) -> List[Campus]:
        with self.app.app_context():
            session = db.session  # FIXME: Create new session?

            campus1 = Campus.create('Testcampus', 'ctst', [], 'mock://campus_ctst/', session=session)
            campus2 = Campus.create('Campus Omega', 'com', [], 'mock://campus_com/', session=session)
            campus3 = Campus.create('Campus Paardenmarkt', 'cpm', [], 'mock://campus_cpm/', session=session)
            campus3.set_active(False)
            session.commit()

            return [campus1, campus2, campus3]

    def activate_feature(self, feature_id: str, user_list: 'List[users.UserId]' = None, available=None) -> Feature:
        with self.app.app_context():
            session = db.session  # FIXME: Create new session?

            feature = Feature.create(feature_id, session=session)

            if user_list:
                for user in user_list:
                    user_obj = AppUser.find_by_id(user.provider, user.id)
                    if user_obj is None:
                        raise ValueError()
                    Feature.set_user_participating(user_obj, feature.string_id, True, session=session)

            if available is not None:
                feature.globally_available = available

            session.commit()
            return feature

    def create_menu(self, campus: Campus, day: datetime.date, items: 'List[menu_item]', session=None) -> Menu:
        def _run():
            menu = Menu.create(campus, day, session=session)

            for item in items:
                translatable, translation = Translatable.get_or_create(item.text, item.language, session=session)
                menu.add_menu_item(translatable, item.type, item.price_students, item.price_staff, session=session)

            return menu

        if session is None:
            with self.app.app_context():
                session = db.session

                result = _run()

                session.commit()
                return result
        else:
            return _run()


class HttpCapture:
    GET = httpretty.GET
    PUT = httpretty.PUT
    POST = httpretty.POST
    DELETE = httpretty.DELETE
    HEAD = httpretty.HEAD
    PATCH = httpretty.PATCH
    OPTIONS = httpretty.OPTIONS
    CONNECT = httpretty.CONNECT

    def __init__(self, allow_net_connect=False):
        self.allow_net_connect = allow_net_connect

    def __enter__(self):
        httpretty.enable(allow_net_connect=self.allow_net_connect)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        httpretty.disable()
        httpretty.reset()

    # noinspection PyMethodMayBeStatic
    def register_uri(self, method, uri, body, status=200):
        httpretty.register_uri(method, uri, body, status=status)
