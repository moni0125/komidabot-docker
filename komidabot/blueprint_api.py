import json
from datetime import date, timedelta
from typing import Any, Dict, TypedDict, Union

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required, UserMixin
from werkzeug.http import HTTP_STATUS_CODES

import komidabot.api_utils as api_utils
import komidabot.messages as messages
import komidabot.models as models
import komidabot.triggers as triggers
import komidabot.web.constants as web_constants
from extensions import db, login
from komidabot.app import get_app
from komidabot.debug.administration import notify_admins
from komidabot.users import UserId
from komidabot.web.users import User as WebUser

blueprint = Blueprint('komidabot api', __name__)
current_user: 'Union[models.RegisteredUser, UserMixin]'


def translatable_to_object(translatable: models.Translatable):
    result = {}
    for translation in translatable.translations:
        result[translation.language] = translation.translation

    return result


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

    if channel == 'administration':
        if not current_user.is_authenticated:
            return login.unauthorized()

        current_user.add_subscription(endpoint, keys)

        db.session.commit()

        return api_utils.response_ok()
    else:
        # FIXME: This code is not really done, but until we can send out daily menus in a consistent manner it'll
        #        have to be this way

        return api_utils.response_bad_request()
        # app = get_app()
        # user: WebUser = app.user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))
        #
        # if user.get_db_user() is None:
        #     user.add_to_db()
        #     user.set_data({
        #         'keys': keys
        #     })
        #
        # # if not channel.user_supported(user):
        # #     return api_utils.response_bad_request()
        #
        # if app.subscription_manager.user_subscribe(user, channel, data=data):
        #     return api_utils.response_ok()
        # else:
        #     return api_utils.response_bad_request()


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

    if channel == 'administration':
        if not current_user.is_authenticated:
            return login.unauthorized()

        current_user.remove_subscription(endpoint)

        db.session.commit()

        return api_utils.response_ok()
    else:
        # FIXME: This code is not really done, but until we can send out daily menus in a consistent manner it'll
        #        have to be this way

        return api_utils.response_bad_request()
        # app = get_app()
        # user: WebUser = app.user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))
        #
        # if user.get_db_user() is None:
        #     return api_utils.response_ok()
        #
        # if app.subscription_manager.user_unsubscribe(user, channel):
        #     return api_utils.response_ok()
        # else:
        #     return api_utils.response_bad_request()


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
    # FIXME: Change admin subscriptions as well? Need to verify this

    # FIXME: This code is not really done, but until we can send out daily menus in a consistent manner it'll
    #        have to be this way

    return api_utils.response_bad_request()


@blueprint.route('/trigger', methods=['POST'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='POST_api_trigger', output_schema='api_response_strict')
@login_required
def post_trigger():
    class PostData(TypedDict):
        trigger: str

    post_data: PostData = request.get_json()
    trigger = post_data['trigger']

    if trigger == 'notification_test_error':
        try:
            raise RuntimeError('Test exception')
        except RuntimeError as e:
            notify_admins(messages.ExceptionMessage(triggers.Trigger(), e))

        return api_utils.response_ok()
    elif trigger == 'notification_test_text':
        notify_admins(messages.TextMessage(triggers.Trigger(), 'Test notification'))

        return api_utils.response_ok()
    elif trigger == 'menu_update':
        from komidabot.komidabot import update_menus

        update_menus()

        return api_utils.response_ok()
    else:
        return api_utils.response_bad_request()


@blueprint.route('/learning', methods=['GET'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(output_schema='GET_api_learning.response')
@login_required
def get_learning():
    datapoint = models.LearningDatapoint.get_random(current_user)

    if datapoint is None:
        return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200], 'data': None}), 200

    processed = json.loads(datapoint.processed_data)

    result = {
        'id': str(datapoint.id),
        'screenshot': datapoint.screenshot,
        'course_name': processed['name']['nl'],
        'course_type': models.CourseType[processed['course_type']].value,
        'course_sub_type': models.CourseSubType[processed['course_sub_type']].value,
        'price_students': processed['price_students'],
        'price_staff': processed['price_staff'],
    }

    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200], 'data': result}), 200


@blueprint.route('/learning', methods=['POST'])
@api_utils.wrap_exceptions
@api_utils.expects_schema(input_schema='POST_api_learning', output_schema='api_response_strict')
@login_required
def post_learning():
    class PostData(TypedDict):
        id: str
        course_name_correct: bool
        course_type: int
        course_sub_type: int
        price_students_correct: bool
        price_staff_correct: bool

    post_data: PostData = request.get_json()

    datapoint = models.LearningDatapoint.find_by_id(int(post_data['id']))

    datapoint.user_submit(current_user, {
        'course_name_correct': post_data['course_name_correct'],
        'course_type': post_data['course_type'],
        'course_sub_type': post_data['course_sub_type'],
        'price_students_correct': post_data['price_students_correct'],
        'price_staff_correct': post_data['price_staff_correct']
    })

    db.session.commit()

    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200


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
