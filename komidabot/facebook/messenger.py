import json, requests, threading
from typing import List
from cachetools import cached, TTLCache

from flask import current_app as app

from komidabot.facebook.message_sender import MessageSender
from komidabot.facebook.message import Message
from komidabot.conversation import MessageReceiver
from komidabot.util import check_exceptions

TYPE_REPLY = 'RESPONSE'
TYPE_SUBSCRIPTION = 'NON_PROMOTIONAL_SUBSCRIPTION'


# TODO: Deprecated
class Messenger:
    def __init__(self, page_access_token: str, admin_ids: List[str]):
        self.session = requests.Session()
        self.base_endpoint = "https://graph.facebook.com/v4.0/"
        self.locale_parameters = {
            'access_token': page_access_token,
            'fields': 'locale'
        }
        self.admin_ids = admin_ids

    @check_exceptions
    def send_message(self, message: 'Message'):
        return app.bot_interfaces['facebook']['api_interface'].post_send_api(message.get_data())

    @staticmethod
    def multicast_message(message: 'Message', recipients: List[MessageReceiver]):
        original_recipient = message.recipient

        for recipient in recipients:
            recipient.send_message(message)

        message.recipient = original_recipient

    @check_exceptions
    def mark_read(self, sender: MessageSender):
        return app.bot_interfaces['facebook']['api_interface'].post_send_api({
            'recipient': {'id': sender.user_id},
            'sender_action': 'mark_seen'
        })

    def is_admin(self, user_id):
        return user_id in self.admin_ids

    @check_exceptions
    @cached(cache=TTLCache(maxsize=64, ttl=300), lock=threading.Lock())
    def lookup_locale(self, user_id):
        response = self.session.get(self.base_endpoint + user_id, params=self.locale_parameters)

        # TODO: Properly handle errors

        # print('Received {} for user request {}'.format(response.status_code, user_id), flush=True)
        # print(response.content, flush=True)

        data = json.loads(response.content)

        return data.get('locale', 'nl_BE')
