import json, requests

from komidabot.util import check_exceptions

BASE_ENDPOINT = 'https://graph.facebook.com/'
API_VERSION = 'v2.11'
SEND_API = '/me/messages'


class ApiInterface:
    def __init__(self, page_access_token: str):
        self.session = requests.Session()
        self.base_endpoint = ""
        self.messages_endpoint = self.base_endpoint + "v2.11/me/messages"

        self.base_parameters = dict()
        self.base_parameters['access_token'] = page_access_token
        self.headers_post = dict()
        self.headers_post['Content-Type'] = 'application/json'

        self.locale_parameters = {
            'access_token': page_access_token,
            'fields': 'locale'
        }

    @check_exceptions  # TODO: Exception checking needs to be done differently
    def post_send_api(self, data: dict):
        # TODO: Could really do with batching (especially for multicasting)

        # TODO: Futures or Promises???

        response = self.session.post(BASE_ENDPOINT + API_VERSION + SEND_API, params=self.base_parameters,
                                     headers=self.headers_post, data=json.dumps(data))

        # print('Received {} for request {}'.format(response.status_code, response.request.body), flush=True)
        # print(response.content, flush=True)

        return response.status_code == 200
