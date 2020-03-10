import datetime
import json
from decimal import Decimal
from typing import Dict, List, Set, Tuple

import requests

import komidabot.models as models
from komidabot.debug.state import DebuggableException, ProgramStateTrace, SimpleProgramState
from komidabot.translation import LANGUAGE_DUTCH, LANGUAGE_ENGLISH

BASE_ENDPOINT = 'https://restickets.uantwerpen.be/'
MENU_API = '{endpoint}api/GetMenuByDate/{campus}/{date}'
PRICE_API = '{endpoint}api/getPriceConversion/{price}'
ALL_MENU_API = '{endpoint}api/GetMenu/{date}'

API_GET_HEADERS = dict()
API_GET_HEADERS['Accept'] = 'application/json'

COURSE_LOGOS_RAW = [
    {"id": 201, "nameNl": "bio", "nameEn": "bio", "logo": "ikoon-bio.gif", "sortorder": 2},
    {"id": 202, "nameNl": "gevogelte", "nameEn": "poultry", "logo": "ikoon-gevogelte.gif", "sortorder": 3},
    {"id": 203, "nameNl": "grill", "nameEn": "grill", "logo": "ikoon-grill.gif", "sortorder": 1},
    {"id": 204, "nameNl": "kaas", "nameEn": "cheese", "logo": "ikoon-kaas.gif", "sortorder": 3},
    {"id": 205, "nameNl": "konijn", "nameEn": "rabbit", "logo": "ikoon-konijn.gif", "sortorder": 3},
    {"id": 206, "nameNl": "lam", "nameEn": "lamb", "logo": "ikoon-lam.gif", "sortorder": 3},
    {"id": 207, "nameNl": "pasta", "nameEn": "pasta", "logo": "ikoon-pasta.gif", "sortorder": 1},
    {"id": 208, "nameNl": "rund", "nameEn": "ox", "logo": "ikoon-rund.gif", "sortorder": 3},
    {"id": 209, "nameNl": "salade", "nameEn": "salad", "logo": "ikoon-salade.gif", "sortorder": 1},
    {"id": 210, "nameNl": "snack", "nameEn": "snack", "logo": "ikoon-snack.gif", "sortorder": 1},
    {"id": 211, "nameNl": "soep", "nameEn": "soup", "logo": "ikoon-soep.gif", "sortorder": 1},
    {"id": 212, "nameNl": "varken", "nameEn": "pig", "logo": "ikoon-varken.gif", "sortorder": 3},
    {"id": 213, "nameNl": "vegan", "nameEn": "vegan", "logo": "ikoon-vegan.gif", "sortorder": 2},
    {"id": 214, "nameNl": "veggie", "nameEn": "veggie", "logo": "ikoon-veggie.gif", "sortorder": 2},
    {"id": 215, "nameNl": "vis", "nameEn": "fish", "logo": "ikoon-vis.gif", "sortorder": 3},
    {"id": 216, "nameNl": "less meat", "nameEn": "less meat", "logo": "ikoon-less.gif", "sortorder": 1},
]

COURSE_LOGOS = {
    'BIO': 201,  # Biological course (???)
    'CHICKEN': 202,  # Contains chicken
    'GRILL': 203,  # Grill course
    'CHEESE': 204,  # Contains cheese
    'RABBIT': 205,  # Contains rabbit
    'LAMB': 206,  # Contains lamb
    'PASTA': 207,  # Pasta course / contains pasta???
    'VEAL': 208,  # Contains veal
    'SALAD': 209,  # Salad course
    'SNACK': 210,  # Sub course
    'SOUP': 211,  # Soup course
    'PIG': 212,  # Contains pig
    'VEGAN': 213,  # Does not contain meats???
    'VEGGIE': 214,  # Vegetarian course
    'FISH': 215,  # Contains fish
    'LESS_MEAT': 216,  # Contains less meat
}


class ExternalCourse:
    def __init__(self, sort_order: int, show_first: bool, main_course: bool,
                 price_students: float):
        self.name = dict()  # type: Dict[str, str]
        self.sort_order = sort_order
        self.show_first = show_first
        self.main_course = main_course

        price_students = Decimal(price_students)
        self.price_students = round(price_students, 2)  # type: Decimal

    def add_name(self, locale, name):
        if locale in self.name:
            raise ValueError('Duplicate name for locale')
        if not name:
            raise ValueError('Empty name')

        self.name[locale] = name

    def __repr__(self):
        return repr(self.name)

    def __lt__(self, other: 'ExternalCourse'):
        if self.show_first:
            if not other.show_first:
                return True
            elif self.main_course:
                return not other.main_course
        elif other.show_first:
            return False
        elif self.main_course:
            return not other.main_course


class ExternalMenuItem:
    def __init__(self, sort_order: int, course_type: models.CourseType, course_sub_type: models.CourseSubType,
                 course_attributes: List[models.CourseAttributes], courses: List[ExternalCourse]):
        self.sort_order = sort_order
        self.course_type = course_type
        self.course_sub_type = course_sub_type
        self.course_attributes = course_attributes
        self.courses = courses[:]
        self.courses.sort()

        self.price_staff = None

    def get_supported_languages(self) -> 'Set[str]':
        result = None
        for elem in self.courses:
            if result is None:
                result = set(elem.name.keys())
            else:
                result = result.intersection(set(elem.name.keys()))

        return result

    def get_combined_text(self, language=LANGUAGE_DUTCH):
        for elem in self.courses:
            if language not in elem.name:
                return None  # No official translation available

        result = ', '.join(elem.name[language] for elem in self.courses)

        # Return string with capitalized first letter
        return result[0].upper() + result[1:]

    def get_student_price(self):
        return sum((item.price_students for item in self.courses if item.price_students), Decimal('0.0'))

    def get_staff_price(self):
        return self.price_staff

    def __repr__(self):
        return '{order} {type} {sub_type} {attributes} {icon} {text} ({price1} / {price2})' \
            .format(order=self.sort_order, icon=models.course_icons_matrix[self.course_type][self.course_sub_type],
                    text=self.get_combined_text(), price1=self.get_student_price(), price2=self.get_staff_price(),
                    type=self.course_type.name, sub_type=self.course_sub_type.name,
                    attributes=[v.name for v in self.course_attributes])


class ExternalMenu:
    def __init__(self):
        self.session = requests.Session()

        self.lookups = []  # type: List[Tuple[models.Campus, datetime.date]]

    def add_to_lookup(self, campus: models.Campus, date: datetime.date):
        self.lookups.append((campus, date))

    def lookup_menus(self) -> 'Dict[Tuple[models.Campus, datetime.date], List[ExternalMenuItem]]':
        debug_state = ProgramStateTrace()
        result = dict()

        for campus, date in self.lookups:
            # Replaced try ... except with context manager
            # try:
            with debug_state.state(SimpleProgramState('Lookup menu', {'campus': campus.short_name, 'date': str(date)})):
                url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus.external_id, date=date.strftime('%Y-%m-%d'))

                response = self.session.get(url, headers=API_GET_HEADERS)
                if 400 <= response.status_code < 500:
                    raise DebuggableException('Client error on HTTP request')
                if 500 <= response.status_code < 600:
                    raise DebuggableException('Server error on HTTP request')

                try:
                    data = json.loads(response.text)
                except json.decoder.JSONDecodeError:
                    # If we fail to decode JSON, this probably means we got an empty response back
                    # This can happen if we try to look up the menu on Sundays or Saturdays
                    continue

                # print(data)

                if data['restaurantId'] != campus.external_id:
                    raise DebuggableException('Got menu for different restaurant')

                items = []

                for item in data['menuItems']:
                    with debug_state.state(SimpleProgramState('Menu item', item)):
                        enabled = item['enabled']
                        sort_order = item['sortorder']
                        menu_contents = []

                        if not enabled:
                            continue

                        combined_logos = []
                        calculate_multi_price = False

                        has_pasta = False

                        for item_content in item['menuItemContents']:
                            with debug_state.state(SimpleProgramState('Menu item ingredient', item_content)):
                                course = item_content['course']
                                enabled = course['enabled']
                                deleted = course['deleted']
                                course_sort_order = item_content['sortOrder']

                                if not enabled or deleted:
                                    continue

                                name_nl = course['dispNameNl']
                                name_en = course['dispNameEn']
                                main_course = course['maincourse']
                                price = course['price']
                                calculate_multi_price = calculate_multi_price or course['calculatedMultiplePrices']
                                fixed_price = course['fixedprice']
                                fixed_multiple_prices = course['fixedMultiplePrices']
                                show_first = course['showFirst']

                                combined_logos += [entry['courseLogoId'] for entry in course['course_CourseLogos']]

                                for pasta in ['spaghetti', 'tagliatelle', 'papardelle', 'bucatini', 'cannelloni',
                                              'ravioli', 'tortellini', 'caramelle', 'penne', 'rigatoni', 'orecchiette',
                                              'farfalle', 'caserecce', 'fusilli', 'pasta', ]:
                                    if pasta in name_nl.lower():
                                        has_pasta = True
                                        break  # Found pasta in the name!

                                course_obj = ExternalCourse(course_sort_order, show_first, main_course, price)
                                course_obj.add_name(LANGUAGE_DUTCH, name_nl.strip())
                                if name_en:
                                    course_obj.add_name(LANGUAGE_ENGLISH, name_en.strip())
                                menu_contents.append(course_obj)

                        if not menu_contents:
                            # If no menu contents (all are disabled), don't add a menu item
                            continue

                        has_pasta = has_pasta or (COURSE_LOGOS['PASTA'] in combined_logos)

                        course_type = models.CourseType.DAILY
                        course_sub_type = models.CourseSubType.NORMAL

                        if COURSE_LOGOS['VEGGIE'] in combined_logos or COURSE_LOGOS['VEGAN'] in combined_logos:
                            course_sub_type = models.CourseSubType.VEGAN

                        if COURSE_LOGOS['SOUP'] in combined_logos:
                            course_type = models.CourseType.SOUP
                        elif COURSE_LOGOS['PASTA'] in combined_logos or has_pasta:
                            course_type = models.CourseType.PASTA
                        elif COURSE_LOGOS['GRILL'] in combined_logos:
                            course_type = models.CourseType.GRILL
                        elif COURSE_LOGOS['SNACK'] in combined_logos:
                            course_type = models.CourseType.SUB
                        elif COURSE_LOGOS['SALAD'] in combined_logos:
                            course_type = models.CourseType.SALAD

                        menu_item = ExternalMenuItem(sort_order, course_type, course_sub_type,
                                                     [models.CourseAttributes(v) for v in combined_logos],
                                                     menu_contents)

                        if calculate_multi_price:
                            url = PRICE_API.format(endpoint=BASE_ENDPOINT, price=menu_item.get_student_price())
                            price_response = self.session.get(url, headers=API_GET_HEADERS)
                            price_data = json.loads(price_response.text)

                            menu_item.price_staff = round(Decimal(price_data['staffprice']), 2)

                        items.append(menu_item)

                items.sort(key=lambda i: (i.course_type.value, i.course_sub_type.value))

                if len(items) > 0:
                    result[(campus, date)] = items
            # except Exception as e:
            #     raise Exception('Failed retrieving menu data for ({}, {})'.format(campus.short_name, date)) from e

        return result
