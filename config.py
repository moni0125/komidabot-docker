import os
from collections import namedtuple
from typing import List, Optional, TypedDict

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

# NOTE: While this is a different namedtuple from UserId, this will still properly handle equality checks between other
#       named tuples (including typing.NamedTuple)
_UserId = namedtuple('_UserId', ['id', 'provider'])


def _get_user(string: str) -> _UserId:
    split = string.split('/', 2)
    if len(split) == 1:
        return _UserId(split[0], 'facebook')
    else:
        return _UserId(split[1], split[0])


def _get_postgres_uri(host, user, password, db):
    if not db:
        raise ValueError('Invalid database')
    if password:
        return f'postgresql://{user}:{password}@{host}:5432/{db}'
    else:
        return f'postgresql://{user}@{host}:5432/{db}'


class ConfigType(TypedDict):
    TESTING: bool
    TESTING: bool
    PRODUCTION: bool
    DISABLED: bool
    VERBOSE: bool
    DUMP_FILE: Optional[str]

    PAGE_ACCESS_TOKEN: Optional[str]
    VERIFY_TOKEN: Optional[str]
    APP_SECRET: Optional[str]

    ADMIN_IDS: List[_UserId]

    VAPID_PRIVATE_KEY: Optional[str]
    VAPID_PUBLIC_KEY: Optional[str]

    AUTH_GOOGLE_CLIENT_ID: Optional[str]
    AUTH_GOOGLE_CLIENT_SECRET: Optional[str]
    AUTH_GOOGLE_DISCOVERY_URL: str

    COVID19_DISABLED: int


class BaseConfig:
    """Base configuration"""
    TESTING = False
    PRODUCTION = False
    DISABLED = int(os.getenv('DISABLED', '0')) != 0
    VERBOSE = int(os.getenv('VERBOSE', '0')) != 0
    DUMP_FILE = os.getenv('DUMP_FILE')

    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    APP_SECRET = os.getenv('APP_SECRET')

    ADMIN_IDS = [_get_user(split) for split in os.getenv('ADMIN_IDS', '').split(':')]

    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')

    AUTH_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    AUTH_GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    AUTH_GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

    COVID19_DISABLED = int(os.getenv('COVID19_DISABLED', '0')) != 0

    # Flask-SQLAlchemy options
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session options
    SESSION_COOKIE_HTTPONLY = True
    SESSION_FILE_DIR = '/var/flask_session'
    SESSION_PERMANENT = False
    SESSION_REFRESH_EACH_REQUEST = False
    SESSION_TYPE = 'filesystem'


class ProductionConfig(BaseConfig):
    """Production configuration"""
    PRODUCTION = True

    # Flask-SQLAlchemy options
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_prod')

    # Flask-Session options
    SESSION_COOKIE_SECURE = True


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    VERBOSE = int(os.getenv('VERBOSE', '1')) != 0

    # Flask-SQLAlchemy options
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_dev')


class TestingConfig(BaseConfig):
    """Testing configuration"""
    DISABLED = False
    VERBOSE = False
    TESTING = True
    PAGE_ACCESS_TOKEN = None
    VERIFY_TOKEN = None
    APP_SECRET = None

    # Flask-SQLAlchemy options
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_test')
