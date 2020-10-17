import functools
import logging

from flask import current_app as _current_app


def get_app() -> 'App':
    return _current_app


class App:
    def __init__(self, config):
        import atexit
        from concurrent.futures import ThreadPoolExecutor as PyThreadPoolExecutor

        import komidabot.ipc as ipc
        from komidabot.facebook.api_interface import ApiInterface
        from komidabot.facebook.constants import PROVIDER_ID as FB_PROVIDER_ID
        from komidabot.facebook.users import UserManager as FBUserManager
        from komidabot.web.constants import PROVIDER_ID as WEB_PROVIDER_ID
        from komidabot.web.users import UserManager as WebUserManager
        from komidabot.komidabot import Komidabot
        from komidabot.translation import GoogleTranslationService, TranslationService
        from komidabot.users import UnifiedUserManager, UserId

        self.logger = self.logger  # type: logging.Logger

        self.bot_interfaces = dict()  # TODO: Deprecate?
        self.bot_interfaces['facebook'] = {
            'api_interface': ApiInterface(config.get('PAGE_ACCESS_TOKEN')),
            'users': FBUserManager()
        }

        self.user_manager = UnifiedUserManager()
        self.user_manager.register_manager(FB_PROVIDER_ID, self.bot_interfaces['facebook']['users'])
        self.user_manager.register_manager(WEB_PROVIDER_ID, WebUserManager())

        self.bot = Komidabot(self)

        self.translator = GoogleTranslationService()  # type: TranslationService

        # TODO: This could probably also be moved to the Komidabot class
        self.task_executor = PyThreadPoolExecutor(max_workers=5)
        atexit.register(PyThreadPoolExecutor.shutdown, self.task_executor)  # Ensure cleanup of resources

        # XXX: Convert from _UserId type in config to the actually used UserId
        self.admin_ids = [UserId(user.id, user.provider) for user in config.get('ADMIN_IDS', [])]

        with self.app_context():
            self.user_manager.initialise()

        if not config['TESTING']:
            def ipc_callback(bot, app_context, data):
                with app_context():
                    bot.handle_ipc(data)

            ipc.start_server(functools.partial(ipc_callback, self.bot, self.app_context))

    def app_context(self):
        raise NotImplementedError()

    @property
    def config(self):
        raise NotImplementedError()

    def _get_current_object(self):
        raise NotImplementedError
