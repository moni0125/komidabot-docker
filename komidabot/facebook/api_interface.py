import json
import threading

import requests
from cachetools import cached, TTLCache

import komidabot.messages as messages
from komidabot.app import get_app
from komidabot.translation import LANGUAGE_DUTCH
from komidabot.util import check_exceptions

BASE_ENDPOINT = 'https://graph.facebook.com/'
API_VERSION = 'v4.0'
SEND_API = '/me/messages'
PROFILE_API = '/me/messenger_profile'


class ApiInterface:
    def __init__(self, page_access_token: str):
        self.session = requests.Session()

        self.base_parameters = dict()
        self.base_parameters['access_token'] = page_access_token
        self.headers_post = dict()
        self.headers_post['Content-Type'] = 'application/json'

        self.locale_parameters = dict()
        self.locale_parameters['access_token'] = page_access_token
        self.locale_parameters['fields'] = 'locale'

    @check_exceptions(messages.MessageSendResult.ERROR)  # Handles exceptions raised in this method
    def post_send_api(self, data: dict) -> messages.MessageSendResult:
        response = self.session.post(BASE_ENDPOINT + API_VERSION + SEND_API, params=self.base_parameters,
                                     headers=self.headers_post, data=json.dumps(data))
        data = json.loads(response.content)

        app = get_app()

        verbose = not app.config.get('TESTING') and not app.config.get('PRODUCTION')

        if verbose:
            print('Received {} for request {}'.format(response.status_code, response.request.body), flush=True)
            print(response.content, flush=True)

        if response.status_code == 200:
            return messages.MessageSendResult.SUCCESS

        if 500 <= response.status_code < 600:
            return messages.MessageSendResult.EXTERNAL_ERROR

        if response.status_code == 400:
            code = data['error']['code']
            subcode = data['error']['error_subcode']

            # https://developers.facebook.com/docs/messenger-platform/reference/send-api/error-codes
            if code == 1200:
                # Temporary send message failure. Please try again later.
                return messages.MessageSendResult.EXTERNAL_ERROR
            if code == 100:
                if subcode == 2018001:
                    # No matching user found
                    return messages.MessageSendResult.GONE
            if code == 10:
                if subcode == 2018065:
                    # This message is sent outside of allowed window.
                    return messages.MessageSendResult.UNREACHABLE
                if subcode == 2018108:
                    # This Person Cannot Receive Messages: This person isn't receiving messages from you right now.
                    return messages.MessageSendResult.UNREACHABLE
            if code == 551:
                if subcode == 1545041:
                    # This person isn't available right now.
                    return messages.MessageSendResult.UNREACHABLE

        return messages.MessageSendResult.ERROR  # TODO: Further specify

    @check_exceptions(False)  # TODO: Exception checking needs to be done differently
    def post_profile_api(self, data: dict):
        response = self.session.post(BASE_ENDPOINT + API_VERSION + PROFILE_API, params=self.base_parameters,
                                     headers=self.headers_post, data=json.dumps(data))

        app = get_app()

        verbose = not app.config.get('TESTING') and not app.config.get('PRODUCTION')

        if verbose:
            print('Received {} for request {}'.format(response.status_code, response.request.body), flush=True)
            print(response.content, flush=True)

        # response.raise_for_status()

        # return True

        return response.status_code == 200

    @check_exceptions()  # TODO: Exception checking needs to be done differently
    @cached(cache=TTLCache(maxsize=64, ttl=300), lock=threading.Lock())
    def lookup_locale(self, user_id):
        # TODO: Futures or Promises???

        response = self.session.get(BASE_ENDPOINT + API_VERSION + user_id, params=self.locale_parameters)

        # print('Received {} for user request {}'.format(response.status_code, user_id), flush=True)
        # print(response.content, flush=True)

        data = json.loads(response.content)

        return data.get('locale', LANGUAGE_DUTCH)
