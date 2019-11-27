import datetime
from decimal import Decimal
from functools import wraps
from typing import Dict, List, NamedTuple, Tuple

import httpretty
from flask.cli import ScriptInfo
from flask_testing import TestCase

import komidabot.models as models
import komidabot.users as users
from app import create_app, db
from komidabot.app import App
from tests.utils import StubTranslator

menu_item = NamedTuple('menu_item', [('type', models.FoodType),
                                     ('text', str),
                                     ('language', str),
                                     ('price_students', Decimal),
                                     ('price_staff', Decimal)])


def with_context(func):
    @wraps(func)
    def decorated_func(self, *args, **kwargs):
        if getattr(with_context, 'active', False):
            return func(self, *args, **kwargs)

        if 'has_context' in kwargs:
            has_context = kwargs.pop('has_context')
            if has_context:
                try:
                    setattr(with_context, 'active', True)
                    return func(self, *args, **kwargs)
                finally:
                    setattr(with_context, 'active', False)

        with self.app.app_context():
            try:
                setattr(with_context, 'active', True)
                return func(self, *args, **kwargs)
            finally:
                setattr(with_context, 'active', False)

    return decorated_func


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

        self.app.translator = self.translator = StubTranslator()

        with self.app.app_context():
            db.create_all()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

        super().tearDown()

    def assertEqualCommutative(self, first, second, msg=None):
        self.assertEqual(first, second, msg=msg)
        self.assertEqual(second, first, msg=msg)

    def assertNotEqualCommutative(self, first, second, msg=None):
        self.assertNotEqual(first, second, msg=msg)
        self.assertNotEqual(second, first, msg=msg)

    @with_context
    def create_translation(self, data: Dict[str, str], default_language: str) -> Tuple[models.Translatable,
                                                                                       Dict[str, models.Translation]]:
        if default_language not in data:
            raise ValueError()

        result = dict()

        translatable, translation = models.Translatable.get_or_create(data[default_language], default_language)

        result[default_language] = translation

        for language, text in data.items():
            if language == default_language:
                continue

            translation = translatable.add_translation(language, text)
            result[language] = translation

        db.session.commit()

        return translatable, result

    @with_context
    def create_test_campuses(self) -> List[models.Campus]:
        campus1 = models.Campus.create('Testcampus', 'ctst', ['keyword1', 'shared_keyword'], 0)
        campus2 = models.Campus.create('Campus Omega', 'com', ['keyword2', 'shared_keyword'], 0)
        campus3 = models.Campus.create('Campus Paardenmarkt', 'cpm', ['keyword3', 'shared_keyword'], 0)
        campus3.active = False
        db.session.commit()

        self.campuses = [campus1, campus2, campus3]

        return self.campuses

    @with_context
    def activate_feature(self, feature_id: str, user_list: 'List[users.UserId]' = None,
                         available=None) -> models.Feature:
        feature = models.Feature.create(feature_id)

        if user_list:
            for user in user_list:
                user_obj = models.AppUser.find_by_id(user.provider, user.id)
                if user_obj is None:
                    raise ValueError()
                models.Feature.set_user_participating(user_obj, feature.string_id, True)

        if available is not None:
            feature.globally_available = available

        db.session.commit()
        return feature

    @with_context
    def create_menu(self, campus: models.Campus, day: datetime.date, items: 'List[menu_item]') -> models.Menu:
        menu = models.Menu.create(campus, day)

        for item in items:
            translatable, _ = models.Translatable.get_or_create(item.text, item.language)
            menu.add_menu_item(translatable, item.type, item.price_students, item.price_staff)

        db.session.commit()
        return menu


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
