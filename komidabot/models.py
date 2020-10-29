import datetime
import enum
import json
import locale
from decimal import Decimal
from typing import Any, Collection, Dict, List, Optional, Tuple, TypedDict

from flask_login import UserMixin
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm.session import make_transient, make_transient_to_detached
from sqlalchemy.sql import expression

from extensions import db
from komidabot.translation import TranslationService
from komidabot.util import expected, expected_or_none

make_transient = make_transient
make_transient_to_detached = make_transient_to_detached

_KEYWORDS_SEPARATOR = ' '


# Main course type
class CourseType(enum.Enum):
    SOUP = 1
    DAILY = 2
    PASTA = 3
    GRILL = 4
    SALAD = 5
    SUB = 6
    DESSERT = 7


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


# Course attributes from external menu
class CourseAllergens(enum.Enum):
    EGG = 200
    WHEAT_GLUTEN = 201
    LUPINE = 202
    MILK_LACTOSE = 203
    MUSTARD = 204
    NUTS = 205
    PEANUTS = 206
    SHELLFISH = 207
    CELERY = 208
    SESAME = 209
    SOY = 210
    SULFITES = 211
    FISH = 212
    MOLLUSKS = 213
    HALAL = 214

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


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
    CourseType.DESSERT: {
        CourseSubType.NORMAL: '🍨',
        CourseSubType.VEGETARIAN: '🍨',
        CourseSubType.VEGAN: '🍨',
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


class AppSettings(db.Model):
    __tablename__ = 'app_settings'

    name = db.Column(db.String(), primary_key=True)
    value = db.Column(db.String(), nullable=False, server_default=json.dumps(None))

    def __init__(self, name: str, value: Any = None):
        if not isinstance(name, str):
            raise ValueError('name expected {} got {}'.format(type(str), type(name)))

        self.name = name
        self.value = json.dumps(value)

    @staticmethod
    def create_entries():
        AppSettings.set_default('registrations_enabled', False)

        db.session.commit()

    @staticmethod
    def set_default(name: str, default: Any) -> 'AppSettings':
        setting = AppSettings.query.filter_by(name=name).first()

        if setting is None:
            setting = AppSettings(name, default)

            db.session.add(setting)

        return setting

    @staticmethod
    def get_value(name: str) -> Any:
        setting = AppSettings.query.filter_by(name=name).first()

        assert setting is not None

        return json.loads(setting.value)


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
            raise expected('name', name, str)
        if not isinstance(short_name, str):
            raise expected('short_name', short_name, str)

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
            raise expected('campus_id', campus_id, int)
        if not isinstance(first_day, datetime.date):
            raise expected('first_day', first_day, datetime.date)
        if last_day is not None and not isinstance(last_day, datetime.date):
            raise expected_or_none('last_day', last_day, datetime.date)
        if not isinstance(translatable_id, int):
            raise expected('translatable_id', translatable_id, int)

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
            raise expected('text', text, str)
        if not isinstance(language, str):
            raise expected('language', language, str)

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
            raise ValueError('language expected (got {})'.format(language))
        if translator is not None and not isinstance(translator, TranslationService):
            raise expected_or_none('translator', translator, TranslationService)

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
            raise expected('translatable_id', translatable_id, int)
        if not isinstance(language, str):
            raise expected('language', language, str)
        if not isinstance(translation, str):
            raise expected('translation', translation, str)
        if provider is not None and not isinstance(provider, str):
            raise expected_or_none('provider', provider, str)

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

    menu_items: 'Collection[MenuItem]' = db.relationship('MenuItem', backref='menu', passive_deletes=True,
                                                         order_by='[MenuItem.course_type, MenuItem.course_sub_type]')

    def __init__(self, campus_id: int, day: datetime.date):
        if not isinstance(campus_id, int):
            raise expected('campus_id', campus_id, int)
        if not isinstance(day, datetime.date):
            raise expected('day', day, datetime.date)

        self.campus_id = campus_id
        self.menu_day = day

    def delete(self):
        db.session.delete(self)

    def add_menu_item(self, translatable: Translatable, course_type: CourseType, course_sub_type: CourseSubType,
                      course_attributes: List[CourseAttributes], course_allergens: List[CourseAllergens],
                      price_students: Decimal, price_staff: Optional[Decimal]) -> 'MenuItem':
        menu_item = MenuItem(self, translatable.id, course_type, course_sub_type, price_students, price_staff)
        menu_item.set_attributes(course_attributes)
        menu_item.set_allergens(course_allergens)

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
    external_id = db.Column(db.Integer(), unique=True, nullable=True, server_default=expression.null())
    course_type = db.Column(db.Enum(CourseType), nullable=False)
    course_sub_type = db.Column(db.Enum(CourseSubType), nullable=False)
    course_attributes = db.Column(db.Text(), nullable=False, default='[]', server_default='[]')
    course_allergens = db.Column(db.Text(), nullable=False, default='[]', server_default='[]')
    price_students = db.Column(db.Numeric(4, 2), nullable=False)
    price_staff = db.Column(db.Numeric(4, 2), nullable=True)
    data_frozen = db.Column(db.Boolean(), nullable=False, server_default=expression.false())

    def __init__(self, menu: Menu, translatable_id: int, course_type: CourseType, course_sub_type: CourseSubType,
                 price_students: Decimal, price_staff: Optional[Decimal]):
        if not isinstance(menu, Menu):
            raise expected('menu', menu, Menu)
        if not isinstance(translatable_id, int):
            raise expected('translatable_id', translatable_id, int)
        if not isinstance(course_type, CourseType):
            raise expected('course_type', course_type, CourseType)
        if not isinstance(course_sub_type, CourseSubType):
            raise expected('course_sub_type', course_sub_type, CourseSubType)
        if not isinstance(price_students, Decimal):
            raise expected('price_students', price_students, Decimal)
        if price_staff is not None and not isinstance(price_staff, Decimal):
            raise expected_or_none('price_staff', price_staff, Decimal)

        self.menu = menu
        self.translatable_id = translatable_id
        self.course_type = course_type
        self.course_sub_type = course_sub_type
        self.price_students = price_students
        self.price_staff = price_staff

    def get_translation(self, language: str, translator: 'TranslationService') -> 'Translation':
        return self.translatable.get_translation(language, translator)

    @staticmethod
    def format_price(price: Decimal) -> str:
        if price == 0.0:
            return ''
        return locale.currency(price).replace(' ', '')

    def get_attributes(self) -> List[CourseAttributes]:
        # Stored as a list of strings or a list of ints (backwards compat)
        return [CourseAttributes(v) if isinstance(v, int) else CourseAttributes[v]
                for v in json.loads(self.course_attributes)]

    def set_attributes(self, attributes: List[CourseAttributes]):
        self.course_attributes = json.dumps([v.name for v in attributes])

    def get_allergens(self) -> List[CourseAllergens]:
        # Stored as a list of strings
        return [CourseAllergens[v] for v in json.loads(self.course_allergens)]

    def set_allergens(self, allergens: List[CourseAllergens]):
        self.course_allergens = json.dumps([v.name for v in allergens])

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
            raise expected('user_id', user_id, int)
        if not isinstance(day, Day):
            raise expected('day', day, Day)
        if not isinstance(campus_id, int):
            raise expected('campus_id', campus_id, int)
        if not isinstance(active, bool):
            raise expected('active', active, bool)

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
            raise expected('provider', provider, str)
        if not isinstance(internal_id, str):
            raise expected('internal_id', internal_id, str)
        if not isinstance(language, str):
            raise expected('language', language, str)

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
    def create(provider: str, internal_id: str, language: str) -> 'AppUser':
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
            raise expected('string_id', string_id, str)
        if description is not None and not isinstance(description, str):
            raise expected_or_none('description', description, str)
        if globally_available is not None and not isinstance(globally_available, bool):
            raise expected_or_none('globally_available', globally_available, bool)

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
            raise expected('user_id', user_id, int)
        if not isinstance(feature_id, int):
            raise expected('feature_id', feature_id, int)

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


class RegisteredUser(db.Model, UserMixin):
    __tablename__ = 'registered_user'

    id = db.Column(db.String(), primary_key=True)
    provider = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    profile_picture = db.Column(db.String(), nullable=False)
    enabled = db.Column(db.Boolean(), nullable=False, server_default=expression.false())
    web_subscriptions = db.Column(db.String(), nullable=False, server_default='[]')

    submissions = db.relationship('LearningDatapointSubmission', backref='registered_user', passive_deletes=True)

    def __init__(self, provider: str, user_id: str, name: str, email: str, profile_picture: str):
        if not isinstance(user_id, str):
            raise expected('user_id', user_id, str)
        if not isinstance(name, str):
            raise expected('name', name, str)
        if not isinstance(provider, str):
            raise expected('provider', provider, str)
        if not isinstance(email, str):
            raise expected('email', email, str)
        if not isinstance(profile_picture, str):
            raise expected('profile_picture', profile_picture, str)

        self.id = user_id
        self.provider = provider
        self.name = name
        self.email = email
        self.profile_picture = profile_picture

    @staticmethod
    def create(provider: str, user_id: str, name: str, email: str, profile_picture: str) -> 'RegisteredUser':
        user = RegisteredUser(provider, user_id, name, email, profile_picture)

        db.session.add(user)

        return user

    @staticmethod
    def find_by_serialized_id(serialized: str) -> 'Optional[RegisteredUser]':
        return RegisteredUser.find_by_id(*json.loads(serialized))

    def get_id(self):
        return json.dumps([self.provider, self.id])

    @staticmethod
    def find_by_id(provider: str, user_id: str) -> 'Optional[RegisteredUser]':
        return RegisteredUser.query.filter_by(provider=provider, id=user_id).first()

    @staticmethod
    def find_by_email(email: str) -> 'Optional[RegisteredUser]':
        return RegisteredUser.query.filter_by(email=email).first()

    @staticmethod
    def get_all() -> 'List[RegisteredUser]':
        return RegisteredUser.query.all()

    @staticmethod
    def get_all_verified() -> 'List[RegisteredUser]':
        return RegisteredUser.query.filter_by(enabled=True).all()

    def delete(self):
        db.session.delete(self)

    @property
    def is_active(self):
        return self.enabled

    def get_subscriptions(self) -> 'List[AdminSubscription]':
        return json.loads(self.web_subscriptions)

    def set_subscriptions(self, subscriptions: 'List[AdminSubscription]'):
        self.web_subscriptions = json.dumps(subscriptions)

    def add_subscription(self, endpoint: str, keys: Dict[str, str]):
        subscriptions: 'List[AdminSubscription]' = []
        found = False

        for sub in self.get_subscriptions():
            subscriptions.append(sub)

            if sub['endpoint'] == endpoint:
                found = True

        if not found:
            subscriptions.append({'endpoint': endpoint, 'keys': keys})

        self.set_subscriptions(subscriptions)

    def remove_subscription(self, endpoint: str):
        self.set_subscriptions([sub for sub in self.get_subscriptions() if sub['endpoint'] != endpoint])

    @staticmethod
    def replace_subscription(old_endpoint: str, endpoint: str, keys: Dict[str, str]):
        for user in RegisteredUser.get_all():
            user.set_subscriptions([sub if sub['endpoint'] != old_endpoint else {'endpoint': endpoint, 'keys': keys}
                                    for sub in user.get_subscriptions()])

    def __hash__(self):
        return hash((self.id, self.provider))


class AdminSubscription(TypedDict):
    endpoint: str  # XXX: This is a globally unique identifier for the client
    keys: Dict[str, str]


class LearningDatapoint(db.Model):
    __tablename__ = 'learning_datapoint'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    menu_day = db.Column(db.Date(), nullable=False)
    screenshot = db.Column(db.Text(), nullable=False)
    processed_data = db.Column(db.Text(), nullable=False)

    submissions = db.relationship('LearningDatapointSubmission', backref='datapoint', passive_deletes=True)

    def __init__(self, campus_id: str, menu_day: datetime.date, screenshot: Any, processed_data: Any):
        if not isinstance(campus_id, str):
            raise expected('campus_id', campus_id, str)
        if not isinstance(menu_day, datetime.date):
            raise expected_or_none('menu_day', menu_day, datetime.date)
        if screenshot is None:
            raise ValueError('screenshot expected not None')
        if processed_data is None:
            raise ValueError('processed_data expected not None')

        self.campus_id = campus_id
        self.menu_day = menu_day
        self.screenshot = json.dumps(screenshot)
        self.processed_data = json.dumps(processed_data)

    @staticmethod
    def create(campus_id: str, menu_day: datetime.date, screenshot: Any,
               processed_data: Any) -> 'Optional[LearningDatapoint]':
        datapoint = LearningDatapoint(campus_id, menu_day, screenshot, processed_data)

        db.session.add(datapoint)

        return datapoint

    @staticmethod
    def find_by_id(datapoint_id: int) -> 'Optional[LearningDatapoint]':
        return LearningDatapoint.query.filter_by(id=datapoint_id).first()

    @staticmethod
    def get_all() -> 'List[LearningDatapoint]':
        return LearningDatapoint.query.all()

    @staticmethod
    def get_random(user: RegisteredUser) -> 'Optional[LearningDatapoint]':
        return LearningDatapoint.query.order_by(expression.func.random()).filter(
            expression.not_(
                LearningDatapointSubmission.query.filter(
                    LearningDatapoint.id == LearningDatapointSubmission.datapoint_id,
                    LearningDatapointSubmission.user_id == user.id
                ).exists()
            )
        ).first()

    def user_submit(self, user: RegisteredUser, submission_data: Any):
        LearningDatapointSubmission.create(self, user, submission_data)

    def __hash__(self):
        return hash(self.id)


class LearningDatapointSubmission(db.Model):
    __tablename__ = 'learning_datapoint_submission'

    user_id = db.Column(db.String(),
                        primary_key=True)
    user_provider = db.Column(db.String(16),
                              primary_key=True)
    datapoint_id = db.Column(db.Integer(),
                             db.ForeignKey('learning_datapoint.id', onupdate='CASCADE', ondelete='CASCADE'),
                             primary_key=True)
    submission_data = db.Column(db.Text(), nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(('user_id', 'user_provider'),
                                ['registered_user.id', 'registered_user.provider'],
                                onupdate='CASCADE',
                                ondelete='CASCADE'),
    )

    def __init__(self, user_id: str, user_provider: str, datapoint_id: int, submission_data: Any):
        if not isinstance(user_id, str):
            raise expected('user_id', user_id, str)
        if not isinstance(user_provider, str):
            raise expected('user_provider', user_provider, str)
        if not isinstance(datapoint_id, int):
            raise expected('datapoint_id', datapoint_id, int)
        if submission_data is None:
            raise ValueError('submission_data expected not None')

        self.user_id = user_id
        self.user_provider = user_provider
        self.datapoint_id = datapoint_id
        self.submission_data = json.dumps(submission_data)

    @staticmethod
    def create(datapoint: LearningDatapoint, user: RegisteredUser,
               submission_data: Any) -> 'Optional[LearningDatapointSubmission]':
        submission = LearningDatapointSubmission(user.id, user.provider, datapoint.id, submission_data)

        db.session.add(submission)

        return submission

    def __hash__(self):
        return hash((self.user_id, self.user_provider, self.datapoint_id))


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
