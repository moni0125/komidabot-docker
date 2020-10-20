import datetime
import enum
import json
import locale
from decimal import Decimal
from typing import Collection, Dict, List, Optional, Tuple

from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm.session import make_transient, make_transient_to_detached
from sqlalchemy.sql import expression

import komidabot.util as util
from extensions import db
from komidabot.translation import TranslationService

make_transient = make_transient
make_transient_to_detached = make_transient_to_detached

_KEYWORDS_SEPARATOR = ' '


# TODO: Convert FoodType to be a CourseType and CourseSubType
class FoodType(enum.Enum):
    SOUP = 1  # -> (SOUP, NORMAL)
    MEAT = 2  # -> (DAILY, NORMAL)
    VEGAN = 3  # -> (DAILY, VEGAN)
    GRILL = 4  # -> (GRILL, NORMAL)
    PASTA_MEAT = 5  # -> (PASTA, NORMAL)
    PASTA_VEGAN = 6  # -> (PASTA, VEGAN)
    SALAD = 7  # -> (SALAD, NORMAL)
    SUB = 8  # -> (SUB, NORMAL)


# Main course type
class CourseType(enum.Enum):
    SOUP = 1
    DAILY = 2
    PASTA = 3
    GRILL = 4
    SALAD = 5
    SUB = 6


# Course sub-type
class CourseSubType(enum.Enum):
    NORMAL = 1
    VEGETARIAN = 2
    VEGAN = 3


# Course attributes from external menu
class CourseAttributes(enum.Enum):
    BIO = 201
    CHICKEN = 202
    GRILL = 203
    CHEESE = 204
    RABBIT = 205
    LAMB = 206
    PASTA = 207
    VEAL = 208
    SALAD = 209
    SNACK = 210
    SOUP = 211
    PIG = 212
    VEGAN = 213
    VEGGIE = 214
    FISH = 215
    LESS_MEAT = 216

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


food_type_icons = {
    FoodType.SOUP: '🍵',
    FoodType.MEAT: '🥩',
    FoodType.VEGAN: '🥬',
    FoodType.GRILL: '🍖',
    FoodType.PASTA_MEAT: '🍝',
    FoodType.PASTA_VEGAN: '🍝',
    FoodType.SALAD: '🥗',
    FoodType.SUB: '🥖',
}

course_icons_matrix = {
    CourseType.SOUP: {
        CourseSubType.NORMAL: '🍵',
        CourseSubType.VEGETARIAN: '🍵',
        CourseSubType.VEGAN: '🍵',
    },
    CourseType.DAILY: {
        CourseSubType.NORMAL: '🥩',
        CourseSubType.VEGETARIAN: '🥬',
        CourseSubType.VEGAN: '🥬',
    },
    CourseType.PASTA: {
        CourseSubType.NORMAL: '🍝',
        CourseSubType.VEGETARIAN: '🍝',
        CourseSubType.VEGAN: '🍝',
    },
    CourseType.GRILL: {
        CourseSubType.NORMAL: '🍖',
        CourseSubType.VEGETARIAN: '🍖',
        CourseSubType.VEGAN: '🍖',
    },
    CourseType.SALAD: {
        CourseSubType.NORMAL: '🥗',
        CourseSubType.VEGETARIAN: '🥗',
        CourseSubType.VEGAN: '🥗',
    },
    CourseType.SUB: {
        CourseSubType.NORMAL: '🥖',
        CourseSubType.VEGETARIAN: '🥖',
        CourseSubType.VEGAN: '🥖',
    },
}

food_to_course_type_mapping = {
    FoodType.SOUP: (CourseType.SOUP, CourseSubType.NORMAL),
    FoodType.MEAT: (CourseType.DAILY, CourseSubType.NORMAL),
    FoodType.VEGAN: (CourseType.DAILY, CourseSubType.VEGETARIAN),
    FoodType.GRILL: (CourseType.GRILL, CourseSubType.NORMAL),
    FoodType.PASTA_MEAT: (CourseType.PASTA, CourseSubType.NORMAL),
    FoodType.PASTA_VEGAN: (CourseType.PASTA, CourseSubType.VEGETARIAN),
    FoodType.SALAD: (CourseType.SALAD, CourseSubType.NORMAL),
    FoodType.SUB: (CourseType.SUB, CourseSubType.NORMAL),
}

course_to_food_type_mapping = {
    CourseType.SOUP: {
        CourseSubType.NORMAL: FoodType.SOUP,
        CourseSubType.VEGETARIAN: FoodType.SOUP,
        CourseSubType.VEGAN: FoodType.SOUP,
    },
    CourseType.DAILY: {
        CourseSubType.NORMAL: FoodType.MEAT,
        CourseSubType.VEGETARIAN: FoodType.VEGAN,
        CourseSubType.VEGAN: FoodType.VEGAN,
    },
    CourseType.PASTA: {
        CourseSubType.NORMAL: FoodType.PASTA_MEAT,
        CourseSubType.VEGETARIAN: FoodType.PASTA_VEGAN,
        CourseSubType.VEGAN: FoodType.PASTA_VEGAN,
    },
    CourseType.GRILL: {
        CourseSubType.NORMAL: FoodType.GRILL,
        CourseSubType.VEGETARIAN: FoodType.GRILL,
        CourseSubType.VEGAN: FoodType.GRILL,
    },
    CourseType.SALAD: {
        CourseSubType.NORMAL: FoodType.SALAD,
        CourseSubType.VEGETARIAN: FoodType.SALAD,
        CourseSubType.VEGAN: FoodType.SALAD,
    },
    CourseType.SUB: {
        CourseSubType.NORMAL: FoodType.SUB,
        CourseSubType.VEGETARIAN: FoodType.SUB,
        CourseSubType.VEGAN: FoodType.SUB,
    },
}


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    # Added for compat with datetime.date
    SATURDAY = 6
    SUNDAY = 7


week_days = [Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY]


class Campus(db.Model):
    __tablename__ = 'campus'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    short_name = db.Column(db.String(8), nullable=False)
    # TODO: Wouldn't it be easier to instead have a new table mapping keywords to campuses, resolving possible conflicts
    keywords = db.Column(db.Text(), default='', nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    external_id = db.Column(db.Integer(), nullable=False)

    menus = db.relationship('Menu', backref='campus', passive_deletes=True)
    closing_days = db.relationship('ClosingDays', backref='campus', passive_deletes=True)
    subscriptions = db.relationship('UserDayCampusPreference', backref='campus', passive_deletes=True)

    def __init__(self, name: str, short_name: str):
        if not isinstance(name, str):
            raise ValueError('name')
        if not isinstance(short_name, str):
            raise ValueError('short_name')

        self.name = name
        self.short_name = short_name.lower()
        self._set_keywords([short_name, ])

    def get_keywords(self) -> List[str]:
        return self.keywords.split(_KEYWORDS_SEPARATOR)

    def add_keyword(self, keyword: str):
        if _KEYWORDS_SEPARATOR in keyword:
            raise ValueError('Cannot have a space (the separator) in a keyword: {}'.format(repr(keyword)))

        self._set_keywords(self.get_keywords() + [keyword.lower(), ])

    def remove_keyword(self, keyword: str):
        self._set_keywords([kw for kw in self.get_keywords() if kw != keyword])

    def _set_keywords(self, keywords: List[str]):
        separator = _KEYWORDS_SEPARATOR
        # XXX: Add separator at the front and end for queries
        self.keywords = separator + separator.join(set(kw for kw in keywords if kw)) + separator

    @staticmethod
    def create(name: str, short_name: str, keywords: List[str], external_id: int, add_to_db=True) -> 'Campus':
        result = Campus(name, short_name)
        result.external_id = external_id

        for keyword in keywords:
            result.add_keyword(keyword)

        if add_to_db:
            db.session.add(result)

        return result

    @staticmethod
    def get_by_id(campus_id: int) -> 'Optional[Campus]':
        return Campus.query.filter_by(id=campus_id).first()

    @staticmethod
    def get_by_short_name(short_name: str) -> 'Optional[Campus]':
        return Campus.query.filter_by(short_name=short_name).first()

    @staticmethod
    def find_by_keyword(keyword: str) -> 'List[Campus]':
        # XXX: Each keyword is prepended and appended with the separator
        return Campus.query.filter(Campus.keywords.contains(_KEYWORDS_SEPARATOR + keyword.lower() + _KEYWORDS_SEPARATOR,
                                                            autoescape=True)).all()

    @staticmethod
    def get_all() -> 'List[Campus]':
        return Campus.query.order_by(Campus.id).all()

    @staticmethod
    def get_all_active() -> 'List[Campus]':
        return Campus.query.filter_by(active=True).order_by(Campus.id).all()

    def __hash__(self):
        return hash(self.id)


class ClosingDays(db.Model):
    __tablename__ = 'closing_days'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    first_day = db.Column(db.Date(), nullable=False)
    last_day = db.Column(db.Date(), nullable=True, server_default=None)
    translatable_id = db.Column(db.Integer(), db.ForeignKey('translatable.id', onupdate='CASCADE', ondelete='RESTRICT'),
                                nullable=False)

    def __init__(self, campus_id: int, first_day: datetime.date, last_day: datetime.date,
                 translatable_id: int):
        if not isinstance(campus_id, int):
            raise ValueError('campus_id')
        if not isinstance(first_day, datetime.date):
            raise ValueError('first_day')
        if last_day is not None and not isinstance(last_day, datetime.date):
            raise ValueError('last_day')
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')

        self.campus_id = campus_id
        self.first_day = first_day
        self.last_day = last_day
        self.translatable_id = translatable_id

    @staticmethod
    def create(campus: Campus, first_day: datetime.date, last_day: Optional[datetime.date], reason: str, language: str,
               add_to_db=True) -> 'ClosingDays':
        translatable, translation = Translatable.get_or_create(reason, language)

        result = ClosingDays(campus.id, first_day, last_day, translatable.id)

        if add_to_db:
            db.session.add(result)

        return result

    @staticmethod
    def find_is_closed(campus: Campus, day: datetime.date) -> 'Optional[ClosingDays]':
        return ClosingDays.query.filter(db.and_(ClosingDays.campus_id == campus.id,
                                                ClosingDays.first_day <= day,
                                                db.or_(
                                                    ClosingDays.last_day == None,
                                                    ClosingDays.last_day >= day
                                                )
                                                )).first()

    @staticmethod
    def find_closing_days_including(campus: Campus,
                                    start_date: datetime.date,
                                    end_date: datetime.date) -> 'List[ClosingDays]':
        return ClosingDays.query.filter(db.and_(ClosingDays.campus_id == campus.id,
                                                ClosingDays.first_day <= end_date,
                                                db.or_(
                                                    ClosingDays.last_day == None,
                                                    ClosingDays.last_day >= start_date
                                                )
                                                )).all()


class Translatable(db.Model):
    __tablename__ = 'translatable'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    original_language = db.Column(db.String(5), nullable=False)
    original_text = db.Column(db.String(256), nullable=False)

    _translations = db.relationship('Translation', backref='translatable', passive_deletes=True)
    menu_items = db.relationship('MenuItem', backref='translatable')
    closing_days = db.relationship('ClosingDays', backref='translatable')

    def __init__(self, text: str, language: str):
        if not isinstance(text, str):
            raise ValueError('text')
        if not isinstance(language, str):
            raise ValueError('language')

        self.original_language = language
        self.original_text = text

    def add_translation(self, language: str, text: str, provider: str = None) -> 'Translation':
        if sqlalchemy_inspect(self).transient:
            raise ValueError('Translatable is transient and cannot have translations')

        if language == self.original_language:
            return self._get_dummy_translation()

        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is None:
            translation = Translation(self.id, language, text, provider)
            db.session.add(translation)

        return translation

    def get_translation(self, language: str, translator: 'TranslationService' = None) -> 'Translation':
        if not language:
            raise ValueError('language')
        if translator is not None and not isinstance(translator, TranslationService):
            raise ValueError('translator')

        if sqlalchemy_inspect(self).transient:
            raise ValueError('Translatable is transient and cannot have translations')

        if language == self.original_language:
            return self._get_dummy_translation()

        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is None:
            if translator is None:
                raise ValueError('Cannot translate without translator function')

            translation_text = translator.translate(self.original_text, self.original_language, language)

            translation = self.add_translation(language, translation_text, translator.identifier)

        return translation

    def has_translation(self, language: str) -> 'bool':
        if not language:
            raise ValueError('language')

        if sqlalchemy_inspect(self).transient:
            raise ValueError('Translatable is transient and cannot have translations')

        if language == self.original_language:
            return True

        return db.session.query(Translation.query.filter_by(translatable_id=self.id,
                                                            language=language).exists()).scalar()

    @property
    def translations(self) -> 'Collection[Translation]':
        return (self._get_dummy_translation(), *list(self._translations))

    def _get_dummy_translation(self) -> 'Translation':
        translation = getattr(self, '_dummy_translation', None)
        if translation is None:
            # Make a fake Translation object
            translation = Translation(self.id, self.original_language, self.original_text)
            make_transient_to_detached(translation)

        setattr(self, '_dummy_translation', translation)
        return translation

    @staticmethod
    def get_or_create(text: str, language) -> 'Tuple[Translatable, Translation]':
        translatable = Translatable.query.filter_by(original_language=language, original_text=text).first()

        if translatable is None:
            translatable = Translatable(text, language)
            db.session.add(translatable)
            db.session.flush()

        return translatable, translatable.get_translation(language, None)

    @staticmethod
    def get_by_id(translatable_id) -> 'Optional[Translatable]':
        return Translatable.query.filter_by(id=translatable_id).first()

    def __hash__(self):
        return hash(self.id)


class Translation(db.Model):
    __tablename__ = 'translation'

    translatable_id = db.Column(db.Integer(), db.ForeignKey('translatable.id', onupdate='CASCADE', ondelete='CASCADE'),
                                primary_key=True)
    language = db.Column(db.String(5), primary_key=True)
    translation = db.Column(db.String(256), nullable=False)
    provider = db.Column(db.String(16))

    def __init__(self, translatable_id: int, language: str, translation: str, provider: str = None):
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')
        if not isinstance(language, str):
            raise ValueError('language')
        if not isinstance(translation, str):
            raise ValueError('translation')
        if provider is not None and not isinstance(provider, str):
            raise ValueError('provider')

        self.translatable_id = translatable_id
        self.language = language
        self.translation = translation
        self.provider = provider

    def __eq__(self, other: 'Translation'):
        if self.translatable_id != other.translatable_id:
            return False
        if self.language != other.language:
            return False
        if self.translation != other.translation:
            return False
        return True

    def __hash__(self):
        return hash((self.translatable_id, self.language))


class Menu(db.Model):
    __tablename__ = 'menu'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    menu_day = db.Column(db.Date(), nullable=False)

    menu_items = db.relationship('MenuItem', backref='menu', passive_deletes=True,
                                 order_by='[MenuItem.course_type, MenuItem.course_sub_type]')

    def __init__(self, campus_id: int, day: datetime.date):
        if not isinstance(campus_id, int):
            raise ValueError('campus_id')
        if not isinstance(day, datetime.date):
            raise ValueError('day')

        self.campus_id = campus_id
        self.menu_day = day

    def delete(self):
        db.session.delete(self)

    def update(self, new_menu: 'Menu'):
        old: List[MenuItem] = self.menu_items
        new: List[MenuItem] = new_menu.menu_items

        _, added, removed = util.get_list_diff(old, new)

        for item in removed:
            db.session.delete(item)
        for item in added:
            # FIXME: Is this safe?
            self.menu_items.append(item.copy(self))

    def clear(self):
        items = list(self.menu_items)

        for item in items:
            db.session.delete(item)

    def add_menu_item(self, translatable: Translatable, course_type: CourseType, course_sub_type: CourseSubType,
                      course_attributes: List[CourseAttributes], price_students: Decimal,
                      price_staff: Optional[Decimal]) -> 'MenuItem':
        menu_item = MenuItem(self.id, translatable.id, course_type, course_sub_type, price_students, price_staff)
        menu_item.set_attributes(course_attributes)

        # FIXME: Is this safe?
        self.menu_items.append(menu_item)

        return menu_item

    @staticmethod
    def create(campus: Campus, day: datetime.date, add_to_db=True) -> 'Menu':
        menu = Menu(campus.id, day)

        if add_to_db:
            db.session.add(menu)

        return menu

    @staticmethod
    def get_menu(campus: Campus, day: datetime.date) -> 'Optional[Menu]':
        return Menu.query.filter_by(campus_id=campus.id, menu_day=day).first()

    @staticmethod
    def remove_menus_on_closing_days():
        rows = Menu.query.filter(
            ClosingDays.query.filter(
                Menu.campus_id == ClosingDays.campus_id,
                Menu.menu_day >= ClosingDays.first_day,
                Menu.menu_day <= ClosingDays.last_day
            ).exists()
        ).all()

        for row in rows:
            db.session.delete(row)

    def __hash__(self):
        return hash(self.id)


class MenuItem(db.Model):
    __tablename__ = 'menu_item'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    menu_id = db.Column(db.Integer(), db.ForeignKey('menu.id', onupdate='CASCADE', ondelete='CASCADE'),
                        nullable=False)
    translatable_id = db.Column(db.Integer(), db.ForeignKey('translatable.id', onupdate='CASCADE', ondelete='RESTRICT'),
                                nullable=False)
    food_type = db.Column(db.Enum(FoodType), nullable=False)
    course_type = db.Column(db.Enum(CourseType), nullable=False)
    course_sub_type = db.Column(db.Enum(CourseSubType), nullable=False)
    course_attributes = db.Column(db.Text(), nullable=False, default='[]', server_default='[]')
    price_students = db.Column(db.Numeric(4, 2), nullable=False)
    price_staff = db.Column(db.Numeric(4, 2), nullable=True)

    def __init__(self, menu_id: int, translatable_id: int, course_type: CourseType, course_sub_type: CourseSubType,
                 price_students: Decimal, price_staff: Optional[Decimal]):
        if menu_id is not None and not isinstance(menu_id, int):  # FIXME: Allowing a null ID is a dirty hack
            raise ValueError('menu_id')
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')
        if not isinstance(course_type, CourseType):
            raise ValueError('course_type')
        if not isinstance(course_sub_type, CourseSubType):
            raise ValueError('course_sub_type')
        if not isinstance(price_students, Decimal):
            raise ValueError('price_students')
        if price_staff is not None and not isinstance(price_staff, Decimal):
            raise ValueError('price_staff')

        self.menu_id = menu_id
        self.translatable_id = translatable_id
        self.food_type = course_to_food_type_mapping[course_type][course_sub_type]
        self.course_type = course_type
        self.course_sub_type = course_sub_type
        self.price_students = price_students
        self.price_staff = price_staff

    def copy(self, menu: Menu):
        result = MenuItem(menu.id, self.translatable_id, self.course_type, self.course_sub_type, self.price_students,
                          self.price_staff)
        result.set_attributes(self.get_attributes())
        return result

    def get_translation(self, language: str, translator: 'TranslationService') -> 'Translation':
        return self.translatable.get_translation(language, translator)

    @staticmethod
    def format_price(price: Decimal) -> str:
        if price == 0.0:
            return ''
        return locale.currency(price).replace(' ', '')

    def get_attributes(self) -> List[CourseAttributes]:
        return [CourseAttributes(v) for v in json.loads(self.course_attributes)]

    def set_attributes(self, attributes: List[CourseAttributes]):
        self.course_attributes = json.dumps([v.value for v in attributes])

    def __lt__(self, other: 'MenuItem') -> bool:
        return (self.course_type, self.course_sub_type, self.translatable_id, self.id) < \
               (other.course_type, other.course_sub_type, other.translatable_id, other.id)

    def __eq__(self, other: 'MenuItem') -> bool:
        if self is other or (self.id is not None and self.id == other.id):  # FIXME: Allowing a null ID is a dirty hack
            return True
            # menu_id is ignored
        if self.translatable_id != other.translatable_id:
            return False
        if self.course_type != other.course_type:
            return False
        if self.course_sub_type != other.course_sub_type:
            return False
        if self.course_attributes != other.course_attributes:
            return False
        if self.price_students != other.price_students:
            return False
        if self.price_staff != other.price_staff:
            return False
        return True

    def __hash__(self):
        return hash(self.id)


class UserDayCampusPreference(db.Model):
    __tablename__ = 'user_day_campus_preference'

    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    day = db.Column(db.Enum(Day), primary_key=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id', onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False)

    # FIXME: Move this out of this table and instead store this in some subscription info table for daily_menu channel
    active = db.Column(db.Boolean(), default=True, nullable=False)

    def __init__(self, user_id: int, day: Day, campus_id: int, active=True) -> None:
        if not isinstance(user_id, int):
            raise ValueError('user_id')
        if not isinstance(day, Day):
            raise ValueError('day')
        if not isinstance(campus_id, int):
            raise ValueError('campus_id')
        if not isinstance(active, bool):
            raise ValueError('active')

        self.user_id = user_id
        self.day = day
        self.campus_id = campus_id
        self.active = active

    @staticmethod
    def get_all_for_user(user: 'AppUser') -> 'List[UserDayCampusPreference]':
        return UserDayCampusPreference.query.filter_by(user_id=user.id).all()

    @staticmethod
    def get_for_user(user: 'AppUser', day: Day) -> 'Optional[UserDayCampusPreference]':
        return UserDayCampusPreference.query.filter_by(user_id=user.id, day=day).first()

    @staticmethod
    def create(user: 'AppUser', day: Day, campus: Campus, active=True) -> 'Optional[UserDayCampusPreference]':
        if day in [Day.SATURDAY, Day.SUNDAY]:
            raise ValueError('Day cannot be SATURDAY or SUNDAY')

        subscription = UserDayCampusPreference(user.id, day, campus.id, active)

        db.session.add(subscription)

        return subscription

    def __hash__(self):
        return hash((self.user_id, self.day))


class AppUser(db.Model):
    __tablename__ = 'app_user'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    provider = db.Column(db.String(32), nullable=False)  # String ID of the provider
    internal_id = db.Column(db.String(), nullable=False)  # ID that is specific to the provider
    language = db.Column(db.String(5), nullable=False)
    # Flag indicating whether a user has been informed about the new site or not
    notified_new_site = db.Column(db.Boolean(), nullable=False, default=False, server_default=expression.false())
    enabled = db.Column(db.Boolean(), nullable=False, default=True, server_default=expression.true())
    data = db.Column(db.Text(), nullable=True)  # Stores data specific to the provider

    __table_args__ = (
        db.UniqueConstraint('provider', 'internal_id'),
    )

    subscriptions = db.relationship('UserDayCampusPreference', backref='user', passive_deletes=True)
    feature_participations = db.relationship('FeatureParticipation', backref='user', passive_deletes=True)

    def __init__(self, provider: str, internal_id: str, language: str):
        if not isinstance(provider, str):
            raise ValueError('provider')
        if not isinstance(internal_id, str):
            raise ValueError('internal_id')
        if not isinstance(language, str):
            raise ValueError('language')

        self.provider = provider
        self.internal_id = internal_id
        self.language = language

    def set_campus(self, day: Day, campus: Campus, active=None):
        sub = UserDayCampusPreference.get_for_user(self, day)
        if sub is None:
            UserDayCampusPreference.create(self, day, campus, active=True if active is None else active)
        else:
            sub.campus = campus
            if active is not None:
                sub.active = active

    def set_day_active(self, day: Day, active: bool):
        sub = UserDayCampusPreference.get_for_user(self, day)
        if sub is None:
            if active:
                raise ValueError('Cannot set subscription active if there is no campus set')
        else:
            sub.active = active

    def get_campus(self, day: Day) -> 'Optional[Campus]':
        sub = UserDayCampusPreference.get_for_user(self, day)
        if sub is not None:
            return sub.campus
        else:
            return None

    def get_subscription(self, day: Day) -> 'Optional[UserDayCampusPreference]':
        return UserDayCampusPreference.get_for_user(self, day)

    def set_language(self, language: str):
        self.language = language

    def set_active(self, day: Day, active: bool):
        sub = UserDayCampusPreference.get_for_user(self, day)
        if sub is None:
            raise ValueError('User does not have a subscription on day {}'.format(day.name))

        sub.active = active

    @staticmethod
    def create(provider: str, internal_id: str, language: str):
        user = AppUser(provider, internal_id, language)

        db.session.add(user)

        return user

    def delete(self):
        db.session.delete(self)

    @staticmethod
    def find_subscribed_users_by_day(day: Day, provider=None) -> 'List[AppUser]':
        q = AppUser.query
        if provider:
            q = q.filter_by(provider=provider)

        return q.join(AppUser.subscriptions).filter(db.and_(UserDayCampusPreference.day == day,
                                                            UserDayCampusPreference.active == expression.true(),
                                                            AppUser.enabled == expression.true()
                                                            )).order_by(AppUser.provider, AppUser.internal_id).all()

    @staticmethod
    def find_by_id(provider: str, internal_id: str) -> 'Optional[AppUser]':
        return AppUser.query.filter_by(provider=provider, internal_id=internal_id).first()

    @staticmethod
    def find_by_provider(provider: str) -> 'List[AppUser]':
        return AppUser.query.filter_by(provider=provider).order_by(AppUser.internal_id).all()

    def __hash__(self):
        return hash(self.id)


class Feature(db.Model):
    __tablename__ = 'feature'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    string_id = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.Text())
    globally_available = db.Column(db.Boolean(), default=False, nullable=False)

    participations = db.relationship('FeatureParticipation', backref='feature', passive_deletes=True)

    def __init__(self, string_id: str, description: str = None, globally_available=False):
        if not isinstance(string_id, str):
            raise ValueError('string_id')
        if description is not None and not isinstance(description, str):
            raise ValueError('description')
        if globally_available is not None and not isinstance(globally_available, bool):
            raise ValueError('globally_available')

        self.string_id = string_id
        self.description = description
        self.globally_available = globally_available

    @staticmethod
    def create(string_id: str, description: str = None, globally_available=False) -> 'Optional[Feature]':
        feature = Feature(string_id, description, globally_available)

        db.session.add(feature)

        return feature

    @staticmethod
    def find_by_id(string_id: str) -> 'Optional[Feature]':
        return Feature.query.filter_by(string_id=string_id).first()

    @staticmethod
    def get_all() -> 'List[Feature]':
        return Feature.query.all()

    @staticmethod
    def is_user_participating(user: Optional[AppUser], string_id: str) -> bool:
        feature = Feature.find_by_id(string_id)
        if feature is None:
            return False

        if feature.globally_available:
            return True

        if user is None:
            return False

        return FeatureParticipation.get_for_user(user, feature) is not None

    @staticmethod
    def set_user_participating(user: AppUser, string_id: str, participating: bool):
        feature = Feature.find_by_id(string_id)
        participation = FeatureParticipation.get_for_user(user, feature)

        if participating:
            if not participation:
                FeatureParticipation.create(user, feature)
        else:
            if participation:
                db.session.delete(feature)

    def __hash__(self):
        return hash(self.id)


class FeatureParticipation(db.Model):
    __tablename__ = 'feature_participation'

    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    feature_id = db.Column(db.Integer(), db.ForeignKey('feature.id', onupdate='CASCADE', ondelete='CASCADE'),
                           primary_key=True)

    def __init__(self, user_id: int, feature_id: int):
        if not isinstance(user_id, int):
            raise ValueError('user_id')
        if not isinstance(feature_id, int):
            raise ValueError('feature_id')

        self.user_id = user_id
        self.feature_id = feature_id

    @staticmethod
    def create(user: AppUser, feature: Feature) -> 'Optional[FeatureParticipation]':
        participation = FeatureParticipation(user.id, feature.id)

        db.session.add(participation)

        return participation

    @staticmethod
    def get_for_user(user: AppUser, feature: Feature) -> 'Optional[FeatureParticipation]':
        return FeatureParticipation.query.filter_by(user_id=user.id, feature_id=feature.id).first()

    def __hash__(self):
        return hash((self.user_id, self.feature_id))


def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


# noinspection PyUnusedLocal
def create_standard_values():
    cst = Campus.create('Stadscampus', 'cst', ['stad', 'stadscampus'], 1)
    cde = Campus.create('Campus Drie Eiken', 'cde', ['drie', 'eiken'], 2)
    cmi = Campus.create('Campus Middelheim', 'cmi', ['middelheim'], 3)
    cgb = Campus.create('Campus Groenenborger', 'cgb', ['groenenborger'], 4)
    cmu = Campus.create('Campus Mutsaard', 'cmu', ['mutsaard'], 5)
    hzs = Campus.create('Hogere Zeevaartschool', 'hzs', ['hogere', 'zeevaartschool'], 6)
    hzs.active = False
    db.session.commit()


def import_dump(dump_file):
    campus_dict: Dict[str, Campus] = dict()

    def get_campus(short_name) -> Campus:
        if short_name not in campus_dict:
            campus_dict[short_name] = Campus.get_by_short_name(short_name)
        return campus_dict[short_name]

    with open(dump_file) as file:
        _ = file.readline()  # Skip header

        line = file.readline()
        while line:
            line = line.strip()
            split = list(line.split('\t'))

            if len(split) == 8:
                split[1] = split[1] == 'True'
            if split[7] == '0':
                split[7] = ''  # Query locale

            user = AppUser.create('facebook', split[0], split[7])
            user.set_campus(Day.MONDAY, get_campus(split[2]), active=split[1])
            user.set_campus(Day.TUESDAY, get_campus(split[3]), active=split[1])
            user.set_campus(Day.WEDNESDAY, get_campus(split[4]), active=split[1])
            user.set_campus(Day.THURSDAY, get_campus(split[5]), active=split[1])
            user.set_campus(Day.FRIDAY, get_campus(split[6]), active=split[1])

            db.session.add(user)

            line = file.readline()

        db.session.commit()
