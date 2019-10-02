import logging, os
from concurrent.futures import ThreadPoolExecutor

from flask.cli import ScriptInfo

from flask import Flask

from komidabot.facebook.api_interface import ApiInterface
from komidabot.facebook.messenger import Messenger
from komidabot.facebook.users import UserManager as FacebookUserManager
from komidabot.conversation_manager import ConversationManager
from komidabot.komidabot import Komidabot
from komidabot.users import UnifiedUserManager

from extensions import db

_task_executor = ThreadPoolExecutor(max_workers=5)


def create_app(script_info: ScriptInfo = None):
    # instantiate the app
    app = Flask(__name__)

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    if script_info is not None and 'APP_SETTINGS' in script_info.data:
        app_settings = script_info.data['APP_SETTINGS']
    app.config.from_object(app_settings)

    # print("The script config is", script_info)
    # print("The database URI is", app.config.get('SQLALCHEMY_DATABASE_URI'))

    # set up extensions
    db.init_app(app)

    # register blueprints
    from komidabot.blueprint import blueprint
    app.register_blueprint(blueprint, url_prefix='/webhook')
    app.register_blueprint(blueprint, url_prefix='/webhook-dev')

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {'app': app, 'db': db}

    app.logger.setLevel(logging.DEBUG)

    app.bot_interfaces = dict()
    app.bot_interfaces['facebook'] = {
        'api_interface': ApiInterface(app.config.get('PAGE_ACCESS_TOKEN')),
        'messenger': Messenger(app.config.get('PAGE_ACCESS_TOKEN'), app.config.get('ADMIN_IDS')),
        'users': FacebookUserManager()
    }

    app.user_manager = UnifiedUserManager()
    app.user_manager.register_manager('facebook', app.bot_interfaces['facebook']['users'])

    app.messenger = app.bot_interfaces['facebook']['messenger']
    app.komidabot = Komidabot()
    app.conversations = ConversationManager()
    app.task_executor = _task_executor

    return app
