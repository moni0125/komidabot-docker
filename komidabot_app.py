import atexit, schedule, logging, os, time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from flask.cli import ScriptInfo

from flask import Flask

from komidabot.facebook.api_interface import ApiInterface
from komidabot.facebook.messenger import Messenger
from komidabot.facebook.users import UserManager as FacebookUserManager
from komidabot.conversation_manager import ConversationManager
from komidabot.triggers import SubscriptionTrigger
from komidabot.komidabot import Komidabot
from komidabot.users import UnifiedUserManager

from extensions import db


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

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print(" * Starting worker processes with PID {}".format(os.getpid()), flush=True)

        # TODO: Check if we need to initialise the database and blueprints only once as well

        # The app is not in debug mode or we are in the reloaded process
        app.bot_interfaces = dict()  # TODO: Deprecate?
        app.bot_interfaces['facebook'] = {
            'api_interface': ApiInterface(app.config.get('PAGE_ACCESS_TOKEN')),
            'messenger': Messenger(app.config.get('PAGE_ACCESS_TOKEN'), app.config.get('ADMIN_IDS_LEGACY')),
            'users': FacebookUserManager()
        }

        app.user_manager = UnifiedUserManager()
        app.user_manager.register_manager('facebook', app.bot_interfaces['facebook']['users'])

        app.messenger = app.bot_interfaces['facebook']['messenger']
        app.komidabot = app.bot = Komidabot()  # TODO: Deprecate app.komidabot?
        app.conversations = ConversationManager()
        app.task_executor = ThreadPoolExecutor(max_workers=5)

        if app.debug:
            # TODO: This is not the right place for this
            app.scheduler = schedule.Scheduler()
            # app.scheduler.every().day.at('10:00').do(partial(Komidabot.trigger_received, app.bot,
            #                                                  SubscriptionTrigger.INSTANCE))
            # FIXME: Temporary
            app.scheduler.every().hour.at(':17').do(partial(Komidabot.trigger_received, app.bot, SubscriptionTrigger()))

            def schedule_executor(task_executor, scheduler):
                while not task_executor._shutdown:
                    scheduler.run_pending()
                    time.sleep(5)

            app.task_executor.submit(schedule_executor, app.task_executor, app.scheduler)

        # Ensure cleanup of resources
        atexit.register(ThreadPoolExecutor.shutdown, app.task_executor)

    return app
