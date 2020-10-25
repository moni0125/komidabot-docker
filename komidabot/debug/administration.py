import copy
import json
from typing import Any, Callable, NoReturn

from pywebpush import webpush, WebPushException

import komidabot.messages as messages
import komidabot.models as models
from komidabot.app import get_app

VAPID_CLAIMS = {
    'sub': 'mailto:komidabot@gmail.com'
}


def notify_admins(message: messages.Message):
    target: Callable[[models.AdminSubscription, Any], NoReturn]

    if isinstance(message, messages.TextMessage):
        target = _send_text_message
    else:
        raise ValueError('Unsupported message type')

    for user in models.RegisteredUser.get_all():
        for sub in user.get_subscriptions():
            message_result = target(sub, message)

            if message_result == messages.MessageSendResult.GONE:
                # Gone = User no longer exists, delete from database
                user.remove_subscription(sub['endpoint'])


def _send_notification(subscription: models.AdminSubscription, data) -> messages.MessageSendResult:
    app = get_app()

    try:
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(data),
            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=copy.deepcopy(VAPID_CLAIMS)
        )

        if app.config.get('VERBOSE'):
            print('Received {} for push {}'.format(response.status_code, subscription['endpoint']), flush=True)
            print(response.content, flush=True)

        return messages.MessageSendResult.SUCCESS
    except WebPushException as e:
        response = e.response

        if app.config.get('VERBOSE'):
            print('Received {} for push {}'.format(response.status_code, subscription['endpoint']), flush=True)
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


def _send_text_message(subscription: models.AdminSubscription,
                       message: messages.TextMessage) -> messages.MessageSendResult:
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

    return _send_notification(copy.deepcopy(subscription), data)
