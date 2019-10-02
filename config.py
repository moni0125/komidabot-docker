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
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(':')

    DISABLED = int(os.getenv('DISABLED', '0')) != 0

    DUMP_FILE = os.getenv('DUMP_FILE')
