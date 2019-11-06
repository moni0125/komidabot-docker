import datetime
import json
from typing import Dict, List, Optional, Tuple

import requests

import komidabot.models as models

BASE_ENDPOINT = 'https://restickets.uantwerpen.be/'
MENU_API = '{endpoint}api/GetMenuByDate/{campus}/{date}'
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
                 price_students: float, price_staff: Optional[float]):
        self.name = dict()  # type: Dict[str, str]
        self.sort_order = sort_order
        self.show_first = show_first
        self.main_course = main_course
        self.price_students = price_students
        self.price_staff = price_staff

    def add_name(self, locale, name):
        if locale in self.name:
            raise ValueError('Duplicate name for locale')
        if not name:
            raise ValueError('Empty name')

        self.name[locale] = name

    def __repr__(self):
        return repr(self.name)

    def __lt__(self, other: 'ExternalCourse'):
        if self.main_course:
            if not other.main_course:
                return True
            elif self.show_first:
                return not other.show_first
        elif other.main_course:
            return False
        elif self.show_first:
            return not other.show_first


class ExternalMenuItem:
    def __init__(self, sort_order: int, food_type: models.FoodType, courses: List[ExternalCourse]):
        self.sort_order = sort_order
        self.food_type = food_type
        self.courses = courses

    def sort_courses(self):
        self.courses.sort()

    def get_combined_text(self):
        self.sort_courses()
        head = self.courses[0]
        tail = self.courses[1:]

        if len(tail) > 0:
            front = tail[:-1]
            last = tail[-1]
            if len(front) > 0:
                extra = '{} en {}'.format(', '.join([elem.name['nl_BE'] for elem in front]), last.name['nl_BE'])
            else:
                extra = last

            return '{} met {}'.format(head.name['nl_BE'], extra)
        else:
            return head.name['nl_BE']

    def __repr__(self):
        return '{} {} {}'.format(self.sort_order, models.food_type_icons[self.food_type], self.get_combined_text())


class ExternalMenu:
    def __init__(self):
        self.lookups = []  # type: List[Tuple[models.Campus, datetime.date]]

    def add_to_lookup(self, campus: models.Campus, date: datetime.date):
        self.lookups.append((campus, date))

    def lookup_menus(self) -> 'Dict[Tuple[models.Campus, datetime.date], List[ExternalMenuItem]]':
        result = dict()

        for campus, date in self.lookups:
            url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus.external_id, date=date.strftime('%Y-%m-%d'))

            response = requests.get(url, headers=API_GET_HEADERS)
            response.raise_for_status()

            data = json.loads(response.content)

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

                has_pasta = False

                for item_content in item['menuItemContents']:
                    course = item_content['course']
                    enabled = course['enabled']
                    course_sort_order = item_content['sortOrder']

                    if not enabled:
                        continue

                    name_nl = course['dispNameNl']
                    name_en = course['dispNameEn']
                    main_course = course['maincourse']
                    price = course['price']
                    staff_price = None
                    calculate_multi_price = course['calculatedMultiplePrices']
                    fixed_price = course['fixedprice']
                    show_first = course['showFirst']

                    if calculate_multi_price:
                        pass  # FIXME: Get staff price

                    combined_logos += [entry['courseLogoId'] for entry in course['course_CourseLogos']]

                    if main_course:
                        for pasta in ['spaghetti', 'tagliatelle', 'papardelle', 'bucatini', 'cannelloni', 'ravioli',
                                      'tortellini', 'caramelle', 'penne', 'rigatoni', 'orecchiette', 'farfalle',
                                      'caserecce', 'fusilli', 'pasta', ]:
                            if pasta in name_nl.lower():
                                has_pasta = True
                                break

                    course_obj = ExternalCourse(course_sort_order, show_first, main_course, price, staff_price)
                    course_obj.add_name('nl_BE', name_nl.strip())
                    if name_en:
                        course_obj.add_name('en_US', name_en.strip())
                    menu_contents.append(course_obj)

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
                    vegan = COURSE_LOGOS['VEGGIE'] in combined_logos
                    if has_pasta:
                        course_type = models.FoodType.PASTA_VEGAN if vegan else models.FoodType.PASTA_MEAT
                    else:
                        course_type = models.FoodType.VEGAN if vegan else models.FoodType.MEAT

                menu_item = ExternalMenuItem(sort_order, course_type, menu_contents)

                items.append(menu_item)

            result[(campus, date)] = items

        return result
