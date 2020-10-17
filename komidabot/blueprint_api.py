import sys
import traceback
from datetime import date, timedelta
from functools import wraps
from typing import Any, Dict, Optional, TypedDict

from flask import Blueprint, abort, jsonify, request, session
from werkzeug.http import HTTP_STATUS_CODES

import komidabot.models as models
import komidabot.web.constants as web_constants
from extensions import db
from komidabot.app import get_app
from komidabot.debug.state import DebuggableException
from komidabot.users import UserManager, UserId
from komidabot.web.users import User as WebUser

blueprint = Blueprint('komidabot api', __name__)


class SubscriptionMessage(TypedDict):
    endpoint: str
    keys: Dict[str, str]
    action: Optional[str]
    channel: Optional['SubscriptionMessageChannel']


class SubscriptionMessageChannel(TypedDict):
    channel: str
    action: str
    data: Optional[Any]


def is_logged_in():
    return session.get('logged_in') is not None


# FIXME: In the future, this should ideally be a proper login system, with a database et al connected to it
def check_logged_in(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        if not is_logged_in:
            return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 200

        return func(*args, **kwargs)

    return decorated_func


def wrap_exceptions(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DebuggableException as e:
            app = get_app()
            app.bot.notify_error(e)

            e.print_info(app.logger)

            return jsonify({'status': 500, 'message': HTTP_STATUS_CODES[500]}), 500
        except Exception as e:
            # noinspection PyBroadException
            try:
                get_app().bot.notify_error(e)
            except Exception:
                pass

            traceback.print_tb(e.__traceback__)
            print(e, flush=True, file=sys.stderr)

            return jsonify({'status': 500, 'message': HTTP_STATUS_CODES[500]}), 500

    return decorated_func


def translatable_to_object(translatable: models.Translatable):
    result = {}
    for translation in translatable.translations:
        result[translation.language] = translation.translation

    return result


@blueprint.route('/login', methods=['POST'])
@wrap_exceptions
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
@wrap_exceptions
@check_logged_in
def handle_authorized():
    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200


@blueprint.route('/subscribe', methods=['POST'])
@wrap_exceptions
def handle_subscribe():
    bad_request = jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]})

    post_data = request.get_json()  # type: SubscriptionMessage
    app = get_app()

    if not post_data:
        return bad_request, 200

    if 'endpoint' not in post_data or 'keys' not in post_data or ('action' in post_data) == ('channel' in post_data):
        return bad_request, 200

    endpoint = post_data['endpoint']
    keys = post_data['keys']

    if not isinstance(endpoint, str) or not isinstance(keys, dict):
        return bad_request, 200

    needs_commit = False

    user_manager = app.user_manager  # type: UserManager
    user = user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))  # type: WebUser

    action = post_data['action'] if 'action' in post_data else None
    channel = post_data['channel'] if 'channel' in post_data else None

    if isinstance(action, str):
        if action == 'add':
            if user.get_db_user() is None:
                user.add_to_db()
                user.set_data({
                    'keys': keys
                })
                needs_commit = True
        elif action == 'remove':
            user.delete()
        else:
            return bad_request, 200
    elif channel is not None:
        if 'channel' not in channel or 'action' not in channel:
            return bad_request, 200

        if user.get_db_user() is None:
            # No DB user, so deny request
            return bad_request, 200

        channel_name = channel['channel']
        channel_action = channel['action']
        data = channel['data'] if 'data' in channel else None

        if not isinstance(channel_action, str) or not isinstance(channel_name, str):
            return bad_request, 200

        # TODO: Implement a reusable channel system which lets these actions fall through
        if channel_action == 'add':
            pass
        elif channel_action == 'remove':
            pass
        elif channel_action == 'modify':
            pass
        else:
            return bad_request, 200
    else:
        return bad_request, 200

    if needs_commit:
        db.session.commit()

    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200


@blueprint.route('/campus', methods=['GET'])
# TODO: @wrap_exceptions
def get_campus_list():
    """
    Gets a list of all available campuses.
    """

    result = []

    campuses = models.Campus.get_all_active()

    for campus in campuses:
        result.append({
            'id': campus.id,
            'name': campus.name,
            'short_name': campus.short_name,
            # TODO: Needs opening hours
        })

    return jsonify(result)


@blueprint.route('/campus/closing_days/<week_str>', methods=['GET'], defaults={'short_name': None})
@blueprint.route('/campus/<short_name>/closing_days/<week_str>', methods=['GET'])
# TODO: @wrap_exceptions
def get_active_closing_days(short_name: str, week_str: str):
    """
    Gets all currently active closures.
    """

    if short_name is None:
        campuses = models.Campus.get_all_active()
    else:
        campus = models.Campus.get_by_short_name(short_name)

        if campus is None:
            return abort(400)

        campuses = [models.Campus.get_by_short_name(short_name)]

    try:
        week_day = date.fromisoformat(week_str)
    except ValueError:
        return abort(400)

    week_start = week_day + timedelta(days=-week_day.weekday())  # Start on Monday

    result = {}

    for campus in campuses:
        current_campus = result[campus.short_name] = []

        for i in range(5):
            closed_data = models.ClosingDays.find_is_closed(campus, week_start + timedelta(days=i))

            if closed_data is not None:
                current_campus.append({
                    'first_day': closed_data.first_day.isoformat(),
                    'last_day': closed_data.last_day.isoformat() if closed_data.last_day is not None else None,
                    'reason': translatable_to_object(closed_data.translatable),
                })
            else:
                current_campus.append(None)

    return jsonify(result)


@blueprint.route('/campus/<short_name>/menu/<day_str>', methods=['GET'])
# TODO: @wrap_exceptions
def get_menu(short_name: str, day_str: str):
    """
    Gets the menu for a specific campus on a day.
    """
    campus = models.Campus.get_by_short_name(short_name)

    if campus is None:
        return abort(400)

    try:
        day_date = date.fromisoformat(day_str)
    except ValueError:
        return abort(400)

    menu = models.Menu.get_menu(campus, day_date)

    result = []

    if menu is None:
        return jsonify(result)

    for menu_item in menu.menu_items:  # type: models.MenuItem
        value = {
            'course_type': menu_item.course_type.value,
            'course_sub_type': menu_item.course_sub_type.value,
            'translation': translatable_to_object(menu_item.translatable),
        }
        if menu_item.price_students:
            value['price_students'] = str(models.MenuItem.format_price(menu_item.price_students))
        if menu_item.price_staff:
            value['price_staff'] = str(models.MenuItem.format_price(menu_item.price_staff))
        result.append(value)

    return jsonify(result)
