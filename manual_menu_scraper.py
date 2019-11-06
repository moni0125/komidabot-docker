import datetime
import sys

from komidabot.external_menu import ExternalMenu
from komidabot.menu_scraper import Campus, MenuScraper

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cst':
            campus = Campus('Stadscampus', 'cst')
            campus.set_page_url('https://www.uantwerpen.be/nl/studentenleven/eten/stadscampus/')
        elif sys.argv[1] == 'cde':
            campus = Campus('Campus Drie Eiken', 'cde')
            campus.set_page_url('https://www.uantwerpen.be/nl/studentenleven/eten/campus-drie-eiken/')
        else:
            campus = Campus('Campus Middelheim', 'cmi')
            campus.set_external_id(3)
    else:
        campus = Campus('Campus Middelheim', 'cmi')
        campus.set_page_url('https://www.uantwerpen.be/nl/studentenleven/eten/campus-middelheim/')

    if len(sys.argv) > 2:
        dates = [datetime.datetime.strptime(arg, '%Y-%m-%d').date() for arg in sys.argv[2:]]
    else:
        dates = [datetime.datetime.today().date()]

    print('Looking up menu for {}'.format(campus.short_name.upper()))
    for date in dates:
        print('- date: {}'.format(date.strftime('%Y-%m-%d')))

    if campus.external_id:
        menu = ExternalMenu()

        for date in dates:
            menu.add_to_lookup(campus, date)

        result = menu.lookup_menus()

        for (campus, date), items in result.items():
            print('{} @ {}'.format(campus.short_name, date.strftime('%Y-%m-%d')), flush=True)

            for item in items:
                print(item)

    else:
        scraper = MenuScraper(campus)

        print(scraper.find_pdf_location())

        scraper.download_pdf()
        scraper.generate_pictures()
        parse_result = scraper.parse_pdf()

        scraper.full_frame.save('out.png', 'PNG')

        for result in parse_result.parse_results:
            print('{}/{}: {} ({})'.format(result.day.name, result.food_type.name, result.name, result.price))
