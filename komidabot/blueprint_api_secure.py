from flask import Blueprint, jsonify
from flask_httpauth import HTTPDigestAuth
from werkzeug.http import HTTP_STATUS_CODES

from komidabot.app import get_app

blueprint = Blueprint('komidabot api secure', __name__)
auth = HTTPDigestAuth()


@auth.get_password
def get_pw(username):
    if username == 'komidabot':
        app = get_app()
        return app.config['HTTP_AUTHENTICATION_PASSWORD'] or None
    return None


@auth.error_handler
def not_authenticated():
    return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 401


@blueprint.route('/authorized', methods=['GET'])
@auth.login_required
def path_authorized():
    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200
