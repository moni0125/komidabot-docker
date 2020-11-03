import atexit
import datetime
import json
import re
from decimal import Decimal
from typing import Any, Dict, Optional, Union

import requests

import komidabot.models as models
from extensions import db
from komidabot.debug.state import DebuggableException, ProgramStateTrace, SimpleProgramState
from komidabot.rate_limit import Limiter
from komidabot.translation import LANGUAGE_DUTCH

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

COURSE_ALLERGENS_RAW = [
    {"id": 200, "nameNl": "Ei", "nameEn": "Egg", "logo": "Ei.gif"},
    {"id": 201, "nameNl": "Gluten-tarwe", "nameEn": "Wheat gluten", "logo": "Gluten-tarwe.gif"},
    {"id": 202, "nameNl": "Lupine", "nameEn": "Lupine", "logo": "Lupine.gif"},
    {"id": 203, "nameNl": "Melk-lactose", "nameEn": "Milk lactose", "logo": "Melk-lactose.gif"},
    {"id": 204, "nameNl": "Mosterd", "nameEn": "Mustard", "logo": "Mosterd.gif"},
    {"id": 205, "nameNl": "Noten", "nameEn": "nuts", "logo": "Noten.gif"},
    {"id": 206, "nameNl": "Pinda", "nameEn": "Peanut", "logo": "Pinda.gif"},
    {"id": 207, "nameNl": "Schaaldieren", "nameEn": "shellfish", "logo": "Schaaldieren.gif"},
    {"id": 208, "nameNl": "Selderij", "nameEn": "Celery", "logo": "Selderij.gif"},
    {"id": 209, "nameNl": "Sesam", "nameEn": "Sesame", "logo": "Sesam.gif"},
    {"id": 210, "nameNl": "Soja", "nameEn": "soya", "logo": "Soja.gif"},
    {"id": 211, "nameNl": "Sulfiet", "nameEn": "sulfite", "logo": "Sulfiet.gif"},
    {"id": 212, "nameNl": "Vis", "nameEn": "Fish", "logo": "Vis.gif"},
    {"id": 213, "nameNl": "Weekdieren", "nameEn": "mollusks", "logo": "Weekdieren.gif"},
    {"id": 214, "nameNl": "halal", "nameEn": "halal", "logo": "halal.gif"},
]

COURSE_LOGOS: Dict[str, int] = {
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
    'VEGAN': 213,  # Vegan course
    'VEGGIE': 214,  # Vegetarian course
    'FISH': 215,  # Contains fish
    'LESS_MEAT': 216,  # Contains less meat
}

COURSE_LOGOS_REVERSE: Dict[int, str] = {value: key for key, value in COURSE_LOGOS.items()}

COURSE_ALLERGENS = {
    'EGG': 200,
    'WHEAT_GLUTEN': 201,
    'LUPINE': 202,
    'MILK_LACTOSE': 203,
    'MUSTARD': 204,
    'NUTS': 205,
    'PEANUTS': 206,
    'SHELLFISH': 207,
    'CELERY': 208,
    'SESAME': 209,
    'SOY': 210,
    'SULFITES': 211,
    'FISH': 212,
    'MOLLUSKS': 213,
    'HALAL': 214,
}

COURSE_ALLERGENS_REVERSE: Dict[int, str] = {value: key for key, value in COURSE_ALLERGENS.items()}

PASTA_NAMES = ['spaghetti', 'tagliatelle', 'papardelle', 'bucatini', 'cannelloni',
               'ravioli', 'tortellini', 'caramelle', 'penne', 'rigatoni', 'orecchiette',
               'farfalle', 'caserecce', 'fusilli', 'pasta', ]
# Pasta names for those who don't speak Italian
BROKEN_ITALIAN_NAMES = ['spagheti', 'tagliatele', 'papardele', 'bucatinni',
                        'cannellonni', 'canneloni', 'cannellonni', 'raviolli',
                        'tortellinni', 'tortelini', 'tortelinni', 'caramele', 'pene',
                        'rigatonni', 'orecchiete', 'orechiette', 'orechiete', 'farfale',
                        'caserece', 'fusili', ]

session_obj = requests.Session()
limiter = Limiter(5)  # Limit to 5 lookups per second


def _cleanup_session(session: requests.Session):
    session.close()


atexit.register(_cleanup_session, session_obj)


def _convert_price(price_students: Union[str, Decimal]) -> Decimal:
    url = PRICE_API.format(endpoint=BASE_ENDPOINT, price=price_students)
    price_response = session_obj.get(url, headers=API_GET_HEADERS)
    price_data = json.loads(price_response.text)

    return round(Decimal(price_data['staffprice']), 2)


def _decimal_or_none(value: str) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(value)


def fetch_raw(campus: models.Campus, date: datetime.date) -> Optional[Any]:
    debug_state = ProgramStateTrace()

    with debug_state.state(SimpleProgramState('Lookup menu', {'campus': campus.short_name, 'date': date.isoformat()})):
        limiter()

        url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus.external_id, date=date.strftime('%Y-%m-%d'))

        response = session_obj.get(url, headers=API_GET_HEADERS)
        if 400 <= response.status_code < 500:
            raise DebuggableException('Client error on HTTP request')
        if 500 <= response.status_code < 600:
            # raise DebuggableException('Server error on HTTP request')
            return None  # Don't raise an exception when the server fails, we'll just ignore it
            # TODO: Maybe send a notification to admins that we failed requesting data?

        # No content is returned when there is no menu for a campus on a specific day
        if response.status_code == 204:
            return None

        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            # If we fail to decode JSON, this means we got an invalid response back
            # This can (or used to) happen when we try to look up the menu on a Sunday or Saturday
            return None


def parse_fetched(fetched: Dict):
    if fetched is None:
        return None

    debug_state = ProgramStateTrace()

    campus = models.Campus.get_by_id(fetched['restaurantId'])

    result = {
        'date': datetime.datetime.strptime(fetched['menuDate'], '%Y-%m-%dT%H:%M:%S').date().isoformat(),
        'campus': campus.short_name,
        'menu': []
    }

    for raw_item in fetched['menuItems']:
        with debug_state.state(SimpleProgramState('Menu item', raw_item['id'])):
            if raw_item['enabled'] != 1:  # XXX: Spotted in the wild, enabled values of 2!
                continue

            parsed_item = {
                'external_id': raw_item['id'],
                'components': [],
                'price': Decimal(0),
                'multiple_prices': False,
                'sort_order': raw_item['sortorder']
            }

            # Sort components in place
            # XXX: This makes the items order consistent in the output as well
            raw_item['menuItemContents'].sort(key=lambda v: (not v['course']['showFirst'],
                                                             not v['course']['maincourse'],
                                                             v['sortOrder']))

            for raw_item_contents in raw_item['menuItemContents']:
                with debug_state.state(SimpleProgramState('Menu item component', raw_item_contents['id'])):
                    raw_course = raw_item_contents['course']

                    if not raw_course['enabled']:
                        pass  # XXX: Used to skip not enabled, but the official site shows these items anyway (bug?)

                    if raw_course['deleted']:
                        pass  # XXX: Used to skip deleted, but the official site shows these items anyway (bug?)

                    # XXX: Note on names, sometimes these can contain double spaces, so we normalize them.
                    #      We also strip any whitespace from the start and end of the names
                    component = {
                        'name': {
                            'nl': re.sub(r'\s+', ' ', raw_course['dispNameNl']).strip(),
                        },
                        'attributes': [],
                        'allergens': []
                    }

                    if raw_course['dispNameEn']:
                        component['name']['en'] = re.sub(r'\s+', ' ', raw_course['dispNameEn']).strip()

                    parsed_item['price'] += round(Decimal(raw_course['price']), 2)

                    if raw_course['calculatedMultiplePrices'] or raw_course['fixedMultiplePrices']:
                        parsed_item['multiple_prices'] = True

                    for raw_allergens in raw_course['course_Allergens']:
                        component['allergens'].append(COURSE_ALLERGENS_REVERSE[raw_allergens['allergenId']])

                    for raw_logos in raw_course['course_CourseLogos']:
                        component['attributes'].append(COURSE_LOGOS_REVERSE[raw_logos['courseLogoId']])

                    # Ensure consistent output
                    component['allergens'].sort()
                    component['attributes'].sort()

                    parsed_item['components'].append(component)

            if parsed_item['price'] == 0:
                continue  # Items with no price are most likely informational messages, not courses

            parsed_item['price'] = str(parsed_item['price'])

            # XXX: Only add a menu item if there's actually something in it
            if len(parsed_item['components']) > 0:
                result['menu'].append(parsed_item)

    # Ensure consistent output
    result['menu'].sort(key=lambda v: v['external_id'])

    return result


def process_parsed(parsed: Dict):
    if parsed is None:
        return None

    debug_state = ProgramStateTrace()

    result = {
        'date': parsed['date'],
        'campus': parsed['campus'],
        'menu': [],
    }

    for parsed_item in parsed['menu']:
        with debug_state.state(SimpleProgramState('Menu item', parsed_item['external_id'])):
            processed_item = {
                'external_id': parsed_item['external_id'],
                'name': {
                    'nl': [],
                    'en': []
                },
                'course_type': '',
                'course_sub_type': '',
                'course_attributes': set(),
                'course_allergens': set(),
                'price_students': parsed_item['price'],
                'price_staff': None
            }

            for component in parsed_item['components']:
                component: Dict

                with debug_state.state(SimpleProgramState('Menu item component', component)):
                    processed_item['course_attributes'].update(component['attributes'])
                    processed_item['course_allergens'].update(component['allergens'])

                    if 'nl' in processed_item['name']:
                        # If not in here, then a component did not support this language
                        piece = component['name'].get('nl', '')
                        if not piece:
                            # Remove if not every component supports this language
                            del processed_item['name']['nl']
                        else:
                            processed_item['name']['nl'].append(piece)

                    if 'en' in processed_item['name']:
                        # If not in here, then a component did not support this language
                        piece = component['name'].get('en', '')
                        if not piece:
                            # Remove if not every component supports this language
                            del processed_item['name']['en']
                        else:
                            processed_item['name']['en'].append(piece)

            for lang in processed_item['name']:
                name = ', '.join(processed_item['name'][lang])
                name = name[0].upper() + name[1:]
                processed_item['name'][lang] = name

            processed_item['course_attributes'] = list(processed_item['course_attributes'])
            processed_item['course_attributes'].sort()

            processed_item['course_allergens'] = list(processed_item['course_allergens'])
            processed_item['course_allergens'].sort()

            if parsed_item['multiple_prices']:
                processed_item['price_staff'] = str(_convert_price(parsed_item['price']))

            has_pasta = 'PASTA' in processed_item['course_attributes']

            if not has_pasta:
                # No pasta in name, let's check to make sure anyway
                name = processed_item['name']['nl']

                for pasta in PASTA_NAMES + BROKEN_ITALIAN_NAMES:
                    if pasta in name.lower():
                        has_pasta = True
                        break

            course_type = models.CourseType.DAILY
            course_sub_type = models.CourseSubType.NORMAL

            if 'VEGAN' in processed_item['course_attributes']:
                course_sub_type = models.CourseSubType.VEGAN
            elif 'VEGGIE' in processed_item['course_attributes']:
                course_sub_type = models.CourseSubType.VEGETARIAN

            if 'SOUP' in processed_item['course_attributes']:
                course_type = models.CourseType.SOUP
            elif 'PASTA' in processed_item['course_attributes'] or has_pasta:
                course_type = models.CourseType.PASTA
            elif 'GRILL' in processed_item['course_attributes']:
                course_type = models.CourseType.GRILL
            elif 'SNACK' in processed_item['course_attributes']:
                # If the item has a low price, it's more likely to be a snack, not a sub (broodje)
                if Decimal(processed_item['price_students']) < 2.5:
                    course_type = models.CourseType.SNACK
                else:
                    course_type = models.CourseType.SUB
            elif 'SALAD' in processed_item['course_attributes']:
                course_type = models.CourseType.SALAD
            else:
                # If the item has a low price and no other specific logo, it's probably a dessert, not a daily course
                if Decimal(processed_item['price_students']) < 3:
                    course_type = models.CourseType.DESSERT

            processed_item['course_type'] = course_type.name
            processed_item['course_sub_type'] = course_sub_type.name

            result['menu'].append(processed_item)

    return result


def update_menu(processed: Dict):
    if processed is None:
        return None

    debug_state = ProgramStateTrace()

    with debug_state.state(SimpleProgramState('Campus menu update', {'campus': processed['campus'],
                                                                     'date': processed['date']})):
        items = processed['menu']
        if len(items) > 0:
            campus = models.Campus.get_by_short_name(processed['campus'])
            date = datetime.date.fromisoformat(processed['date'])

            menu = models.Menu.get_menu(campus, date)

            if menu is None:
                menu = models.Menu.create(campus, date)

            external_ids = [item['external_id'] for item in items]
            menu_items = {}

            for menu_item in menu.menu_items:
                if menu_item.external_id not in external_ids:  # Also matches if menu_item.external_id is None
                    if not menu_item.data_frozen:
                        # Old item, remove
                        db.session.delete(menu_item)
                else:
                    menu_items[menu_item.external_id] = menu_item

            for item in items:
                translatable, translation = models.Translatable.get_or_create(item['name'][LANGUAGE_DUTCH],
                                                                              LANGUAGE_DUTCH)

                for language in set(item['name'].keys()).difference([LANGUAGE_DUTCH]):
                    if translatable.has_translation(language):
                        translation = translatable.get_translation(language)

                        # Don't replace translation if provider is Komida, as this is the official translation
                        # Likewise, if the provider is not defined, this means it is most likely manually added
                        # Otherwise it's done by Google or some other provider, which is sub-optimal
                        if translation.provider not in [None, 'komida', 'manual']:
                            continue  # XXX: Only continues for loop over languages

                        # Update translation and provider to new values
                        translation.translation = item['name'][language]
                        translation.provider = 'komida'
                    else:
                        translatable.add_translation(language, item['name'][language], 'komida')

                attributes = [models.CourseAttributes[attribute] for attribute in item['course_attributes']]
                allergens = [models.CourseAllergens[allergen] for allergen in item['course_allergens']]

                if item['external_id'] in menu_items:
                    menu_item = menu_items[item['external_id']]
                    if not menu_item.data_frozen:
                        menu_item.translatable = translatable
                        menu_item.course_type = models.CourseType[item['course_type']]
                        menu_item.course_sub_type = models.CourseSubType[item['course_sub_type']]
                        menu_item.set_attributes(attributes)
                        menu_item.set_allergens(allergens)
                        menu_item.price_students = Decimal(item['price_students'])
                        menu_item.price_staff = _decimal_or_none(item['price_staff'])
                else:
                    menu_item = menu.add_menu_item(translatable,
                                                   models.CourseType[item['course_type']],
                                                   models.CourseSubType[item['course_sub_type']],
                                                   attributes, allergens,
                                                   Decimal(item['price_students']),
                                                   _decimal_or_none(item['price_staff']))
                    menu_item.external_id = item['external_id']
