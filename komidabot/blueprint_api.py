from datetime import date, timedelta
from typing import Any, Dict, TypedDict

from flask import Blueprint, abort, jsonify, request, session

import komidabot.api_utils as api_utils
import komidabot.models as models
import komidabot.web.constants as web_constants
from komidabot.app import get_app
from komidabot.users import UserId
from komidabot.web.users import User as WebUser

blueprint = Blueprint('komidabot api', __name__)


def translatable_to_object(translatable: models.Translatable):
    result = {}
    for translation in translatable.translations:
        result[translation.language] = translation.translation

    return result


@blueprint.route('/login', methods=['POST'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='POST_api_login', output_schema='api_response_strict')
def post_login():
    class PostData(TypedDict):
        username: str
        password: str

    post_data: PostData = request.get_json()
    username = post_data['username']
    password = post_data['password']

    app = get_app()

    if username == 'komidabot' and password == app.config['HTTP_AUTHENTICATION_PASSWORD']:
        session.clear()
        session['user_id'] = 'komidabot'
        return api_utils.response_ok()

    return api_utils.response_unauthorized()


@blueprint.route('/authorized', methods=['GET'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(output_schema='api_response_strict')
@api_utils.check_logged_in
def get_authorized():
    return api_utils.response_ok()


@blueprint.route('/subscribe', methods=['POST'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='POST_api_subscribe', output_schema='api_response_strict')
def post_subscribe():
    class PostData(TypedDict):
        endpoint: str
        keys: Dict[str, str]
        channel: str
        data: Any

    post_data: PostData = request.get_json()
    endpoint = post_data['endpoint']
    keys = post_data['keys']
    channel = post_data['channel']
    data = post_data['data'] if 'data' in post_data else None

    app = get_app()
    user: WebUser = app.user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))

    if user.get_db_user() is None:
        user.add_to_db()
        user.set_data({
            'keys': keys
        })

    # if not channel.user_supported(user):
    #     return api_utils.response_bad_request()

    if app.subscription_manager.user_subscribe(user, channel, data=data):
        return api_utils.response_ok()
    else:
        return api_utils.response_bad_request()


@blueprint.route('/subscribe', methods=['DELETE'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='DELETE_api_subscribe', output_schema='api_response_strict')
def delete_subscribe():
    class PostData(TypedDict):
        endpoint: str
        channel: str

    post_data: PostData = request.get_json()
    endpoint = post_data['endpoint']
    channel = post_data['channel']

    app = get_app()
    user: WebUser = app.user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))

    if user.get_db_user() is None:
        return api_utils.response_ok()

    if app.subscription_manager.user_unsubscribe(user, channel):
        return api_utils.response_ok()
    else:
        return api_utils.response_bad_request()


@blueprint.route('/subscribe', methods=['PUT'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='PUT_api_subscribe', output_schema='api_response_strict')
def put_subscribe():
    class PostData(TypedDict):
        old_endpoint: str
        endpoint: str
        keys: Dict[str, str]

    post_data: PostData = request.get_json()
    old_endpoint = post_data['old_endpoint']
    endpoint = post_data['endpoint']
    keys = post_data['keys']

    app = get_app()
    user: WebUser = app.user_manager.get_user(UserId(old_endpoint, web_constants.PROVIDER_ID))

    # FIXME: Change internal ID of user and keys

    return api_utils.response_bad_request()


@blueprint.route('/campus', methods=['GET'])
# TODO: @api_utils.wrap_exceptions
# TODO: @api_utils.expects_schema
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
# TODO: @api_utils.wrap_exceptions
# TODO: @api_utils.expects_schema
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
# TODO: @api_utils.wrap_exceptions
# TODO: @api_utils.expects_schema
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

    for menu_item in menu.menu_items:
        menu_item: models.MenuItem
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
