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
#     PASTA_MEAT = 5    pasta in beschrijving
#     PASTA_VEGAN = 6   ICOON VEGAN + pasta in beschrijving
#     SALAD = 7         ICOON SALADE
#     SUB = 8           ICOON SNACK


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


class ExternalMenuItem:
    pass


class ExternalMenu:
    def __init__(self):
        self.lookups = []  # type: List[Tuple[models.Campus, datetime.date]]

    def add_to_lookup(self, campus: models.Campus, date: datetime.date):
        self.lookups.append((campus, date))

    # FIXME: How are we supposed to discern what is what from this API??
    def lookup_menu(self):
        for campus, date in self.lookups:
            print('{} @ {}'.format(campus.short_name, date.strftime('%Y-%m-%d')), flush=True)

            url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus.external_id, date=date.strftime('%Y-%m-%d'))

            response = requests.get(url, headers=API_GET_HEADERS)
            response.raise_for_status()

            data = json.loads(response.content)

            # print(data)

            if data['restaurantId'] != campus.external_id:
                raise RuntimeError('Got menu for different restaurant!')

            for item in data['menuItems']:
                enabled = item['enabled']
                sort_order = item['sortorder']
                menu_contents = []

                if not enabled:
                    continue

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

                    course_obj = ExternalCourse(course_sort_order, show_first, main_course, price, staff_price)
                    course_obj.add_name('nl_BE', name_nl)
                    course_obj.add_name('en_US', name_en)
                    menu_contents.append(course_obj)

                print(sort_order, menu_contents)
