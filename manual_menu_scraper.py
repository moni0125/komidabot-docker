import datetime
import sys

import komidabot.external_menu as external_menu
from komidabot.debug.state import DebuggableException
from komidabot.models import Campus, course_icons_matrix, CourseType, CourseSubType

if __name__ == '__main__':
    # Setup
    campuses = {
        'cst': Campus.create('Stadscampus', 'cst', [], 1, add_to_db=False),
        'cde': Campus.create('Campus Drie Eiken', 'cde', [], 2, add_to_db=False),
        'cmi': Campus.create('Campus Middelheim', 'cmi', [], 3, add_to_db=False),
        'cgb': Campus.create('Campus Groenenborger', 'cgb', [], 4, add_to_db=False),
        'cmu': Campus.create('Campus Mutsaard', 'cmu', [], 5, add_to_db=False),
        'hzs': Campus.create('Hogere Zeevaartschool', 'hzs', [], 6, add_to_db=False),
    }
    campuses_reverse = {campus.external_id: campus for campus in campuses.values()}


    def get_by_id(campus_id: int):
        return campuses_reverse.get(campus_id, None)


    def get_by_short_name(short_name: str):
        return campuses.get(short_name, None)


    # Replace these methods because we don't have database access
    Campus.get_by_id = get_by_id
    Campus.get_by_short_name = get_by_short_name

    # Actual program logic

    if sys.argv[1] not in campuses:
        raise ValueError('Unknown campus')
    campus = campuses[sys.argv[1]]

    if len(sys.argv) > 2:
        dates = [datetime.datetime.strptime(arg, '%Y-%m-%d').date() for arg in sys.argv[2:]]
    else:
        dates = [datetime.datetime.today().date()]

    for date in dates:
        try:
            data_raw = external_menu.fetch_raw(campus, date)

            data_parsed = external_menu.parse_fetched(data_raw)

            data_processed = external_menu.process_parsed(data_parsed)

            print('{} @ {}'.format(data_processed['campus'], data_processed['date']), flush=True)

            for item in data_processed['menu']:
                icon = course_icons_matrix[CourseType[item['course_type']]][CourseSubType[item['course_sub_type']]]

                print('{external_id} {type} {sub_type} {attributes} {allergens} {icon} {text} ({price1} / {price2})'
                      .format(icon=icon,
                              text=item['name']['nl'],
                              price1=item['price_students'],
                              price2=item['price_staff'],
                              type=item['course_type'],
                              sub_type=item['course_sub_type'],
                              attributes=item['course_attributes'],
                              allergens=item['course_allergens'],
                              external_id=item['external_id'])
                      )
        except DebuggableException as e:
            print(e.get_trace())
