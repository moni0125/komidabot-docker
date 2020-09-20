from flask import Blueprint, jsonify

blueprint = Blueprint('komidabot api secure', __name__)


@blueprint.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify("Pong")
