import copy
import json

from pywebpush import webpush, WebPushException

import komidabot.localisation as localisation
import komidabot.menu
import komidabot.messages as messages
import komidabot.translation as translation
import komidabot.users as users
import komidabot.util as util
import komidabot.web.constants as web_constants
from komidabot.app import get_app
from komidabot.models import CourseType, Menu

VAPID_CLAIMS = {
    'sub': 'mailto:komidabot@gmail.com'
}


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message) -> messages.MessageSendResult:
        if user.id.provider != web_constants.PROVIDER_ID:
            raise ValueError('User id is not for {}'.format(web_constants.PROVIDER_ID))

        if isinstance(message, messages.TextMessage):
            return self._send_text_message(user, message)
        elif isinstance(message, messages.MenuMessage):
            return self._send_menu_message(user, message)
        elif isinstance(message, messages.SubscriptionMenuMessage):
            return self._send_subscription_menu_message(user, message)
        else:
            return messages.MessageSendResult.UNSUPPORTED

    @staticmethod
    def _send_notification(subscription_information, data) -> messages.MessageSendResult:
        app = get_app()

        try:
            response = webpush(
                subscription_info=subscription_information,
                data=json.dumps(data),
                vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
                vapid_claims=copy.deepcopy(VAPID_CLAIMS)
            )

            if app.config.get('VERBOSE'):
                print('Received {} for push {}'.format(response.status_code, subscription_information['endpoint']),
                      flush=True)
                print(response.content, flush=True)

            return messages.MessageSendResult.SUCCESS
        except WebPushException as e:
            response = e.response

            if app.config.get('VERBOSE'):
                print('Received {} for push {}'.format(response.status_code, subscription_information['endpoint']),
                      flush=True)
                print(response.content, flush=True)

            if 500 <= response.status_code < 600:
                return messages.MessageSendResult.EXTERNAL_ERROR

            if response.status_code == 429:  # Too many requests, rate limited
                pass  # TODO: Handle rate-limiting
            if response.status_code == 400:  # Invalid request
                return messages.MessageSendResult.ERROR
            if response.status_code == 404:  # Subscription not found
                return messages.MessageSendResult.GONE
            if response.status_code == 410:  # Subscription has been removed
                return messages.MessageSendResult.GONE
            if response.status_code == 413:  # Payload too large
                return messages.MessageSendResult.ERROR

            return messages.MessageSendResult.ERROR

    @staticmethod
    def _send_text_message(user: users.User, message: messages.TextMessage) -> messages.MessageSendResult:
        subscription_information = copy.deepcopy(user.get_data())
        subscription_information['endpoint'] = user.get_internal_id()

        data = {
            'notification': {
                # 'lang': 'NL',
                'badge': 'https://komidabot.xyz/assets/icons/notification-badge-android-72x72.png',
                'title': 'Komidabot message',
                'body': message.text,
                'vibrate': [],
                'renotify': False,
                'requireInteraction': False,
                'actions': [],
                'silent': False,
            }
        }

        return MessageHandler._send_notification(subscription_information, data)

    @staticmethod
    def _send_menu_message(user: users.User, message: messages.MenuMessage) -> messages.MessageSendResult:
        locale = user.get_locale() or translation.LANGUAGE_DUTCH
        menu = message.menu

        date_str = util.date_to_string(locale, menu.menu_day)

        title = localisation.REPLY_MENU_START(locale).format(campus=menu.campus.name, date=date_str)
        text = komidabot.menu.get_short_menu_text(menu, message.translator, locale,
                                                  CourseType.DAILY, CourseType.PASTA, CourseType.GRILL)

        if text is None or text == '':
            return messages.MessageSendResult.ERROR

        subscription_information = copy.deepcopy(user.get_data())
        subscription_information['endpoint'] = user.get_internal_id()

        data = {
            'notification': {
                'lang': locale,
                'badge': 'https://komidabot.xyz/assets/icons/notification-badge-android-72x72.png',
                'title': title,
                'body': text,
                'renotify': False,
                'requireInteraction': False,
                'actions': [],
                'silent': True,
            }
        }

        return MessageHandler._send_notification(subscription_information, data)

    @staticmethod
    def _send_subscription_menu_message(user: users.User,
                                        message: messages.SubscriptionMenuMessage) -> messages.MessageSendResult:
        campus = user.get_campus_for_day(message.date)
        if campus is None:
            # If no campus for selected day, just success it
            return messages.MessageSendResult.SUCCESS

        locale = user.get_locale() or translation.LANGUAGE_DUTCH

        data = message.get_prepared(campus, locale, user.get_provider_name())

        if data is None:
            menu = Menu.get_menu(campus, message.date)

            date_str = util.date_to_string(locale, menu.menu_day)

            title = localisation.REPLY_MENU_START(locale).format(campus=campus.name, date=date_str)
            text = komidabot.menu.get_short_menu_text(menu, message.translator, locale,
                                                      CourseType.DAILY, CourseType.PASTA, CourseType.GRILL)

            if text is None or text == '':
                return messages.MessageSendResult.ERROR

            data = {
                'notification': {
                    'lang': locale,
                    'badge': 'https://komidabot.xyz/assets/icons/notification-badge-android-72x72.png',
                    'title': title,
                    'body': text,
                    'renotify': False,
                    'requireInteraction': False,
                    'actions': [],
                    'silent': True,
                }
            }

            message.set_prepared(campus, locale, user.get_provider_name(), data)

        subscription_information = copy.deepcopy(user.get_data())
        subscription_information['endpoint'] = user.get_internal_id()

        return MessageHandler._send_notification(subscription_information, copy.deepcopy(data))
