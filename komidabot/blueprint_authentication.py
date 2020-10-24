import json
from typing import Optional, Union

import requests
from flask import abort, Blueprint, redirect, request
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

import komidabot.api_utils as api_utils
import komidabot.config as app_config
from extensions import db, login
from komidabot.app import App, get_app
from komidabot.models import RegisteredUser

blueprint = Blueprint('komidabot authentication', __name__)

google_client: Optional[Union[WebApplicationClient, bool]] = None
google_provider_config = None


def init_google_client(app: App):
    global google_client
    client_id = app.config.get('AUTH_GOOGLE_CLIENT_ID')
    if client_id:
        google_client = WebApplicationClient(client_id)
    else:
        google_client = False


def get_google_provider_cfg():
    global google_provider_config
    if google_provider_config is None:
        google_provider_config = requests.get('https://accounts.google.com/.well-known/openid-configuration').json()
    return google_provider_config


@login.user_loader
def user_loader(user_id):
    return RegisteredUser.find_by_id(user_id)


@login.unauthorized_handler
def unauthorized_handler():
    return api_utils.response_unauthorized()


@blueprint.route('/login', methods=['GET'])
@api_utils.wrap_exceptions
def get_login():
    return redirect(request.base_url + '/google')


@blueprint.route('/login/google', methods=['GET'])
@api_utils.wrap_exceptions
def get_login_google():
    app = get_app()

    if google_client is None:
        init_google_client(app)

    if google_client is False:
        return abort(503)

    google_provider_cfg = get_google_provider_cfg()

    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + '/callback',
        scope=['openid', 'email', 'profile'],
    )
    return redirect(request_uri)


@blueprint.route('/login/google/callback', methods=['GET'])
@api_utils.wrap_exceptions
def get_login_google_callback():
    app = get_app()

    if google_client is None:
        init_google_client(app)

    if google_client is False:
        return abort(503)

    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()

    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config.get('AUTH_GOOGLE_CLIENT_ID'), app.config.get('AUTH_GOOGLE_CLIENT_SECRET')),
    )

    print(token_url, headers, body)

    import pprint
    pprint.pp(token_response.json())
    print(flush=True)

    google_client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return abort(403)

    user = RegisteredUser.find_by_id(unique_id)
    if not user:
        if app_config.is_registrations_enabled():
            user = RegisteredUser.create(unique_id, users_name, users_email, picture)
            db.session.commit()
        else:
            return abort(403)

    login_user(user)

    return redirect('/')


@blueprint.route('/logout', methods=['GET'])
@login_required
def get_logout():
    logout_user()
    return redirect('/')


@blueprint.route('/authorized', methods=['GET'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(output_schema='api_response_strict')
@login_required
def get_authorized():
    return api_utils.response_ok()
