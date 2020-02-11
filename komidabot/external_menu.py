import datetime
import json
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import requests

import komidabot.models as models

BASE_ENDPOINT = 'https://restickets.uantwerpen.be/'
MENU_API = '{endpoint}api/GetMenuByDate/{campus}/{date}'
PRICE_API = '{endpoint}api/getPriceConversion/{price}'
ALL_MENU_API = '{endpoint}api/GetMenu/{date}'

API_GET_HEADERS = dict()
API_GET_HEADERS['Accept'] = 'application/json'

# class FoodType(enum.Enum):
#     SOUP = 1          ICOON SOEP
#     MEAT = 2          ???
#     VEGAN = 3         ICOON VEGAN
#     GRILL = 4         ICOON GRILL
#     PASTA_MEAT = 5    pasta in beschrijving / ICOON PASTA
#     PASTA_VEGAN = 6   ICOON VEGAN + pasta in beschrijving
#     SALAD = 7         ICOON SALADE
#     SUB = 8           ICOON SNACK

COURSE_LOGOS_RAW = [
    {"id": 201, "nameNl": "bio", "nameEn": "", "logo": "ikoon-bio.gif", "sortorder": 2},
    {"id": 202, "nameNl": "gevlogelte", "nameEn": "", "logo": "ikoon-gevogelte.gif", "sortorder": 3},
    {"id": 203, "nameNl": "grill", "nameEn": "", "logo": "ikoon-grill.gif", "sortorder": 1},
    {"id": 204, "nameNl": "kaas", "nameEn": "", "logo": "ikoon-kaas.gif", "sortorder": 3},
    {"id": 205, "nameNl": "konijn", "nameEn": "", "logo": "ikoon-konijn.gif", "sortorder": 3},
    {"id": 206, "nameNl": "lam", "nameEn": "", "logo": "ikoon-lam.gif", "sortorder": 3},
    {"id": 207, "nameNl": "pasta", "nameEn": "", "logo": "ikoon-pasta.gif", "sortorder": 1},
    {"id": 208, "nameNl": "rund", "nameEn": "", "logo": "ikoon-rund.gif", "sortorder": 3},
    {"id": 209, "nameNl": "salade", "nameEn": "", "logo": "ikoon-salade.gif", "sortorder": 1},
    {"id": 210, "nameNl": "snack", "nameEn": "", "logo": "ikoon-snack.gif", "sortorder": 1},
    {"id": 211, "nameNl": "soep", "nameEn": "", "logo": "ikoon-soep.gif", "sortorder": 1},
    {"id": 212, "nameNl": "varken", "nameEn": "", "logo": "ikoon-varken.gif", "sortorder": 3},
    {"id": 213, "nameNl": "vegan", "nameEn": "", "logo": "ikoon-vegan.gif", "sortorder": 2},
    {"id": 214, "nameNl": "veggie", "nameEn": "", "logo": "ikoon-veggie.gif", "sortorder": 2},
    {"id": 215, "nameNl": "vis", "nameEn": "", "logo": "ikoon-vis.gif", "sortorder": 3},
]

COURSE_LOGOS = {
    'GRILL': 203,  # Grill course
    'PASTA': 207,  # Pasta course / contains pasta???
    'SALAD': 209,  # Salad course
    'SNACK': 210,  # Sub course
    'SOUP': 211,  # Soup course
    'CHIKCEN': 202,  # Contains chicken
    'CHEESE': 204,  # Contains cheese
    'RABBIT': 205,  # Contains rabbit
    'LAMB': 206,  # Contains lamb
    'VEAL': 208,  # Contains veal
    'PIG': 212,  # Contains pig
    'FISH': 215,  # Contains fish
    'BIO': 201,  # ???
    'VEGAN': 213,  # Does not contain meats???
    'VEGGIE': 214,  # Vegetarian course
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
    def __init__(self, sort_order: int, food_type: models.FoodType, courses: List[ExternalCourse]):
        self.sort_order = sort_order
        self.food_type = food_type
        self.courses = courses[:]
        self.courses.sort()

        self.price_staff = None

    def get_combined_text(self, language='nl_BE'):
        for elem in self.courses:
            if language not in elem.name:
                return None  # No official translation available

        result = ', '.join(elem.name[language] for elem in self.courses)

        print(self.courses)

        # Return string with capitalized first letter
        return result[0].upper() + result[1:]

        # head = self.courses[0]
        # tail = self.courses[1:]
        #
        # if len(tail) > 0:
        #     def get_tail(l):
        #         front = l[:-1]
        #         last = l[-1]
        #         if len(front) > 0:
        #             return '{}, en {}'.format(', '.join([elem.name['nl_BE'] for elem in front]), last.name['nl_BE'])
        #         else:
        #             return last.name['nl_BE']
        #
        #     if ' met ' in head.name['nl_BE']:
        #         if len(tail) == 1:
        #             return '{} en {}'.format(head.name['nl_BE'], tail[0].name['nl_BE'])
        #         else:
        #             return '{}, {}'.format(head.name['nl_BE'], get_tail(tail))
        #
        #     return '{} met {}'.format(head.name['nl_BE'], get_tail(tail))
        # else:
        #     return head.name['nl_BE']

    def get_student_price(self):
        return sum((item.price_students for item in self.courses if item.price_students), Decimal('0.0'))

    def get_staff_price(self):
        return self.price_staff

    def __repr__(self):
        return '{} {} {} ({} / {})'.format(self.sort_order, models.food_type_icons[self.food_type],
                                           self.get_combined_text(), self.get_student_price(), self.get_staff_price())


class ExternalMenu:
    def __init__(self):
        self.session = requests.Session()

        self.lookups = []  # type: List[Tuple[models.Campus, datetime.date]]

    def add_to_lookup(self, campus: models.Campus, date: datetime.date):
        self.lookups.append((campus, date))

    def lookup_menus(self) -> 'Dict[Tuple[models.Campus, datetime.date], List[ExternalMenuItem]]':
        result = dict()

        for campus, date in self.lookups:
            try:
                url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus.external_id, date=date.strftime('%Y-%m-%d'))

                response = self.session.get(url, headers=API_GET_HEADERS)
                response.raise_for_status()

                try:
                    data = json.loads(response.text)
                except json.decoder.JSONDecodeError:
                    continue

                # print(data)

                if data['restaurantId'] != campus.external_id:
                    raise RuntimeError('Got menu for different restaurant!')

                items = []

                for item in data['menuItems']:
                    enabled = item['enabled']
                    sort_order = item['sortorder']
                    menu_contents = []

                    if not enabled:
                        continue

                    combined_logos = []
                    calculate_multi_price = False

                    has_pasta = False

                    for item_content in item['menuItemContents']:
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

                        for pasta in ['spaghetti', 'tagliatelle', 'papardelle', 'bucatini', 'cannelloni', 'ravioli',
                                      'tortellini', 'caramelle', 'penne', 'rigatoni', 'orecchiette', 'farfalle',
                                      'caserecce', 'fusilli', 'pasta', ]:
                            if pasta in name_nl.lower():
                                has_pasta = True
                                break

                        course_obj = ExternalCourse(course_sort_order, show_first, main_course, price)
                        course_obj.add_name('nl_BE', name_nl.strip())
                        if name_en:
                            course_obj.add_name('en_US', name_en.strip())
                        menu_contents.append(course_obj)

                    if not menu_contents:
                        # If no menu contents (all are disabled), don't add a menu item
                        continue

                    has_pasta = has_pasta or (COURSE_LOGOS['PASTA'] in combined_logos)

                    if COURSE_LOGOS['GRILL'] in combined_logos:
                        if COURSE_LOGOS['VEGGIE'] in combined_logos:
                            # SPECIAL CASE! Sometimes the grill can be vegan, so we'll count this as VEGAN for now
                            # TODO: Should a new food category "GRILL_VEGAN" be added?
                            course_type = models.FoodType.VEGAN
                        else:
                            course_type = models.FoodType.GRILL
                    elif COURSE_LOGOS['SOUP'] in combined_logos:
                        course_type = models.FoodType.SOUP
                    elif COURSE_LOGOS['SNACK'] in combined_logos:
                        course_type = models.FoodType.SUB
                    elif COURSE_LOGOS['SALAD'] in combined_logos:
                        course_type = models.FoodType.SALAD
                    else:
                        vegan = (COURSE_LOGOS['VEGGIE'] in combined_logos) or (COURSE_LOGOS['VEGAN'] in combined_logos)
                        if has_pasta:
                            course_type = models.FoodType.PASTA_VEGAN if vegan else models.FoodType.PASTA_MEAT
                        else:
                            course_type = models.FoodType.VEGAN if vegan else models.FoodType.MEAT

                    # If a sort order is set, use it instead
                    # FIXME: Disabled because campuses without hot foods also use the sort order
                    # if sort_order == 1:
                    #     course_type = models.FoodType.VEGAN
                    # elif sort_order == 2:
                    #     course_type = models.FoodType.MEAT
                    # elif sort_order == 3:
                    #     course_type = models.FoodType.PASTA_VEGAN
                    # elif sort_order == 4:
                    #     course_type = models.FoodType.PASTA_MEAT
                    # elif sort_order == 5:
                    #     course_type = models.FoodType.GRILL

                    menu_item = ExternalMenuItem(sort_order, course_type, menu_contents)

                    if calculate_multi_price:
                        url = PRICE_API.format(endpoint=BASE_ENDPOINT, price=menu_item.get_student_price())
                        price_response = self.session.get(url, headers=API_GET_HEADERS)
                        price_data = json.loads(price_response.text)

                        menu_item.price_staff = round(Decimal(price_data['staffprice']), 2)

                    items.append(menu_item)

                items.sort(key=lambda i: i.food_type.value)

                if len(items) > 0:
                    result[(campus, date)] = items
            except Exception as e:
                raise Exception('Failed retrieving menu data for ({}, {})'.format(campus.short_name, date)) from e

        return result
