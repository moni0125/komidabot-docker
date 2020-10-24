import locale
import logging
import os

from flask import Flask
from flask.cli import ScriptInfo
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db, login, migrate, session
from komidabot.app import App as KomidabotApp
from komidabot.features import update_active_features


def create_app(script_info: ScriptInfo = None):
    locale.setlocale(locale.LC_MONETARY, 'nl_BE.utf8')

    # instantiate the app
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    if script_info is not None and 'APP_SETTINGS' in script_info.data:
        app_settings = script_info.data['APP_SETTINGS']
    app.config.from_object(app_settings)

    # print("The script config is", script_info, flush=True)
    # print(" - Data: ", script_info.data, flush=True)
    # print("The database URI is", app.config.get('SQLALCHEMY_DATABASE_URI'), flush=True)

    # set up extensions
    session.init_app(app)
    db.init_app(app)
    migrate.init_app(app)
    login.init_app(app)

    # register blueprints
    from komidabot.blueprint import blueprint as webhook_blueprint
    from komidabot.blueprint_api import blueprint as api_blueprint
    from komidabot.blueprint_authentication import blueprint as authentication_blueprint

    app.register_blueprint(webhook_blueprint, url_prefix='/webhook')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(authentication_blueprint, url_prefix='/api')  # Shares the api prefix

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {'app': app, 'db': db}

    app.logger.setLevel(logging.DEBUG)

    if os.environ.get("KOMIDABOT_SKIP_INITIALISATION") == "true":
        # Don't initialise anything if run from the CLI
        return app

    if app.config['TESTING']:
        # noinspection PyCallByClass,PyTypeChecker
        KomidabotApp.__init__(app, app.config)

        return app

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print(" * Worker processes PID: {}".format(os.getpid()), flush=True)

        with app.app_context():
            update_active_features()

        # TODO: Check if we need to initialise the database and blueprints only once as well

        # The app is not in debug mode or we are in the reloaded process
        # noinspection PyCallByClass,PyTypeChecker
        KomidabotApp.__init__(app, app.config)

    return app
