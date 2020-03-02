from datetime import date, timedelta

from flask import Blueprint, abort, jsonify

import komidabot.models as models

blueprint = Blueprint('komidabot api', __name__)


def translatable_to_object(translatable: models.Translatable):
    result = {}
    for translation in translatable.translations:
        result[translation.language] = translation.translation

    return result


@blueprint.route('/campus', methods=['GET'])
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

    return jsonify({'campuses': result})


@blueprint.route('/campus/closing_days/<day_str>', methods=['GET'], defaults={'short_name': None})
@blueprint.route('/campus/<short_name>/closing_days/<day_str>', methods=['GET'])
def get_active_closing_days(short_name: str, day_str: str):
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

    result = {}

    try:
        day_date = date.fromisoformat(day_str)
    except ValueError:
        return abort(400)

    for campus in campuses:
        closed_data = models.ClosingDays.find_is_closed(campus, day_date)

        if closed_data is not None:
            result[campus.short_name] = {
                'first_day': closed_data.first_day.isoformat(),
                'last_day': closed_data.last_day.isoformat(),
                'reason': str(translatable_to_object(closed_data.translatable)),
            }

    return jsonify({'closing_days': result})


@blueprint.route('/campus/closing_days/<from_str>/<to_str>', methods=['GET'], defaults={'short_name': None})
@blueprint.route('/campus/<short_name>/closing_days/<from_str>/<to_str>', methods=['GET'])
def get_closing_days(short_name: str, from_str: str, to_str: str):
    """
    Gets all closing days encompassing a date range for one or all campuses.
    """

    if short_name is None:
        campuses = models.Campus.get_all_active()
    else:
        campus = models.Campus.get_by_short_name(short_name)

        if campus is None:
            return abort(400)

        campuses = [models.Campus.get_by_short_name(short_name)]

    result = {}

    try:
        from_date = date.fromisoformat(from_str)
        to_date = date.fromisoformat(to_str)
    except ValueError:
        return abort(400)

    for campus in campuses:
        closing_days = []

        for closed_data in models.ClosingDays.find_closing_days_including(campus, from_date, to_date):
            first_day = max(from_date, closed_data.first_day)
            last_day = min(to_date, closed_data.last_day)
            while first_day <= last_day:
                closing_days.append({
                    'date': first_day.isoformat(),
                    'reason': str(translatable_to_object(closed_data.translatable)),
                })

                first_day += timedelta(1)

        closing_days.sort(key=lambda v: v['date'])

        result[campus.short_name] = closing_days

    return jsonify({'closing_days': result})


@blueprint.route('/campus/<short_name>/menu/<day_str>', methods=['GET'])
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
        return jsonify({'menu': result})

    for menu_item in menu.menu_items:  # type: models.MenuItem
        value = {
            'food_type': menu_item.food_type.value,
            'translation': translatable_to_object(menu_item.translatable),
        }
        if menu_item.price_students:
            value['price_students'] = str(menu_item.price_students)
        if menu_item.price_staff:
            value['price_staff'] = str(menu_item.price_staff)
        result.append(value)

    return jsonify({'menu': result})
