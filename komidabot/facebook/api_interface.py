import json
import threading

import requests
from cachetools import cached, TTLCache

from komidabot.app import get_app
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

    @check_exceptions  # TODO: Exception checking needs to be done differently
    def post_send_api(self, data: dict):
        # TODO: Batching is an option, but not beneficial

        # TODO: Futures or Promises???

        response = self.session.post(BASE_ENDPOINT + API_VERSION + SEND_API, params=self.base_parameters,
                                     headers=self.headers_post, data=json.dumps(data))

        app = get_app()

        verbose = not app.config.get('TESTING') and not app.config.get('PRODUCTION')

        if verbose:
            print('Received {} for request {}'.format(response.status_code, response.request.body), flush=True)
            print(response.content, flush=True)

        # response.raise_for_status()

        # return True

        return response.status_code == 200

    @check_exceptions  # TODO: Exception checking needs to be done differently
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

    @check_exceptions  # TODO: Exception checking needs to be done differently
    @cached(cache=TTLCache(maxsize=64, ttl=300), lock=threading.Lock())
    def lookup_locale(self, user_id):
        # TODO: Futures or Promises???

        response = self.session.get(BASE_ENDPOINT + API_VERSION + user_id, params=self.locale_parameters)

        # print('Received {} for user request {}'.format(response.status_code, user_id), flush=True)
        # print(response.content, flush=True)

        data = json.loads(response.content)

        return data.get('locale', 'nl_BE')
