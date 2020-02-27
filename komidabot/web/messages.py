import copy
import json

from pywebpush import webpush, WebPushException

import komidabot.messages as messages
import komidabot.users as users
import komidabot.web.constants as web_constants
from komidabot.app import get_app

VAPID_CLAIMS = {
    'sub': 'mailto:komidabot@gmail.com'
}


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message) -> messages.MessageSendResult:
        if user.id.provider != web_constants.PROVIDER_ID:
            raise ValueError('User id is not for Web')

        if isinstance(message, messages.TextMessage):
            return self._send_text_message(user, message)
        else:
            return messages.MessageSendResult.UNSUPPORTED

    @staticmethod
    def _send_text_message(user: users.User, message: messages.TextMessage) -> messages.MessageSendResult:
        app = get_app()

        subscription_information = copy.deepcopy(user.get_data())
        subscription_information['endpoint'] = user.get_internal_id()

        data = {
            # 'lang': 'NL',
            # 'badge': 'URL',
            'title': 'Komidabot message',
            'body': message.text,
            'vibrate': [],
            'renotify': False,
            'requireInteraction': False,
            'actions': [],
            'silent': False,
        }

        try:
            webpush(
                subscription_info=subscription_information,
                data=json.dumps(data),
                vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
                vapid_claims=copy.deepcopy(VAPID_CLAIMS)
            )

            return messages.MessageSendResult.SUCCESS
        except WebPushException as e:
            status_code = e.response.status_code

            if status_code == 429:  # Too many requests, rate limited
                pass  # TODO: Handle rate-limiting
            if status_code == 400:  # Invalid request
                return messages.MessageSendResult.ERROR
            if status_code == 404:  # Subscription not found
                return messages.MessageSendResult.GONE
            if status_code == 410:  # Subscription has been removed
                return messages.MessageSendResult.GONE
            if status_code == 413:  # Payload too large
                return messages.MessageSendResult.ERROR

            return messages.MessageSendResult.ERROR
