from collections import namedtuple
import os

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

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
        return f'postgres://{user}:{password}@{host}:5432/{db}'
    else:
        return f'postgres://{user}@{host}:5432/{db}'


class BaseConfig:
    """Base configuration"""
    TESTING = False
    PRODUCTION = False
    DISABLED = int(os.getenv('DISABLED', '0')) != 0
    DUMP_FILE = os.getenv('DUMP_FILE')

    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    APP_SECRET = os.getenv('APP_SECRET')

    ADMIN_IDS = [_get_user(split) for split in os.getenv('ADMIN_IDS', '').split(':')]
    ADMIN_IDS_LEGACY = [user.id for user in ADMIN_IDS]

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(BaseConfig):
    """Production configuration"""
    PRODUCTION = True
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_prod')


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_dev')


class TestingConfig(BaseConfig):
    """Testing configuration"""
    DISABLED = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _get_postgres_uri(POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, 'komidabot_test')
