from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.http import HTTP_STATUS_CODES

from komidabot.app import get_app

blueprint = Blueprint('komidabot api secure', __name__)


# FIXME: In the future, this should ideally be a proper login system, with a database et al connected to it


def check_logged_in(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        logged_in = session.get('logged_in')

        if logged_in is None:
            return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 200

        return func(*args, **kwargs)

    return decorated_func


@blueprint.route('/login', methods=['POST'])
def handle_login():
    post_data = request.get_json()

    if not post_data:
        return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200

    if 'username' not in post_data or 'password' not in post_data:
        return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200

    username = post_data['username']
    password = post_data['password']

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200

    app = get_app()

    if username == 'komidabot' and password == app.config['HTTP_AUTHENTICATION_PASSWORD']:
        session.clear()
        session['logged_in'] = True
        return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200

    return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 200


@blueprint.route('/authorized', methods=['GET'])
@check_logged_in
def handle_authorized():
    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200


@blueprint.route('/subscribe', methods=['POST'])
@check_logged_in
def handle_subscribe():
    return jsonify({'status': 501, 'message': HTTP_STATUS_CODES[501]}), 200
