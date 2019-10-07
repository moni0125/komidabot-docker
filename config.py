import os

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB')


class Config:
    TESTING = int(os.getenv('TESTING', '0')) != 0
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f'postgres://{POSTGRES_USER}@{POSTGRES_HOST}:5432/{POSTGRES_DB}'

    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    APP_SECRET = os.getenv('APP_SECRET')
    ADMIN_IDS = [tuple(split.split('/')) for split in os.getenv('ADMIN_IDS', '').split(':')]
    ADMIN_IDS_LEGACY = [id[1] if len(id) > 1 else id[0] for id in ADMIN_IDS]

    DISABLED = int(os.getenv('DISABLED', '0')) != 0

    DUMP_FILE = os.getenv('DUMP_FILE')
