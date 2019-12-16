import datetime
import sys

from komidabot.external_menu import ExternalMenu
from komidabot.models import Campus

if __name__ == '__main__':
    if sys.argv[1] == 'cst':
        campus = Campus('Stadscampus', 'cst')
        campus.external_id = 1
    elif sys.argv[1] == 'cde':
        campus = Campus('Campus Drie Eiken', 'cde')
        campus.external_id = 2
    elif sys.argv[1] == 'cmi':
        campus = Campus('Campus Middelheim', 'cmi')
        campus.external_id = 3
    elif sys.argv[1] == 'cgb':
        campus = Campus('Campus Groenenborger', 'cgb')
        campus.external_id = 4
    elif sys.argv[1] == 'cmu':
        campus = Campus('Campus Mutsaard', 'cmu')
        campus.external_id = 5
    elif sys.argv[1] == 'hzs':
        campus = Campus('Hogere Zeevaartschool', 'hzs')
        campus.external_id = 6
    else:
        raise ValueError('Unknown campus')

    if len(sys.argv) > 2:
        dates = [datetime.datetime.strptime(arg, '%Y-%m-%d').date() for arg in sys.argv[2:]]
    else:
        dates = [datetime.datetime.today().date()]

    print('Looking up menu for {}'.format(campus.short_name.upper()))
    for date in dates:
        print('- date: {}'.format(date.strftime('%Y-%m-%d')))

    menu = ExternalMenu()

    for date in dates:
        menu.add_to_lookup(campus, date)

    result = menu.lookup_menus()

    for (campus, date), items in result.items():
        print('{} @ {}'.format(campus.short_name, date.strftime('%Y-%m-%d')), flush=True)

        for item in items:
            print(item)
