from collections import namedtuple
import os

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB')

_UserId = namedtuple('_UserId', ['id', 'provider'])


def _get_user(string: str) -> _UserId:
    split = string.split('/', 2)
    if len(split) == 1:
        return _UserId(split[0], 'facebook')
    else:
        return _UserId(split[1], split[0])


class Config:
    TESTING = int(os.getenv('TESTING', '0')) != 0
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}@{POSTGRES_HOST}:5432/{POSTGRES_DB}'

    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    APP_SECRET = os.getenv('APP_SECRET')
    ADMIN_IDS = [_get_user(split) for split in os.getenv('ADMIN_IDS', '').split(':')]
    ADMIN_IDS_LEGACY = [user.id for user in ADMIN_IDS]

    DISABLED = int(os.getenv('DISABLED', '0')) != 0

    DUMP_FILE = os.getenv('DUMP_FILE')
