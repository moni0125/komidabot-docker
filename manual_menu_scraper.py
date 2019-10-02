import sys

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
            campus.set_page_url('https://www.uantwerpen.be/nl/studentenleven/eten/campus-middelheim/')
    else:
        campus = Campus('Campus Middelheim', 'cmi')
        campus.set_page_url('https://www.uantwerpen.be/nl/studentenleven/eten/campus-middelheim/')
    scraper = MenuScraper(campus)

    print(scraper.find_pdf_location())

    scraper.download_pdf()
    scraper.generate_pictures()
    parse_result = scraper.parse_pdf()

    scraper.full_frame.save('out.png', 'PNG')

    for result in parse_result.parse_results:
        print('{}/{}: {} ({})'.format(result.day.name, result.food_type.name, result.name, result.price))
