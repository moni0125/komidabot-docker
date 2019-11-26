import datetime
import enum
import locale
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm.session import make_transient, make_transient_to_detached

import komidabot.util as util
from extensions import db

make_transient = make_transient
make_transient_to_detached = make_transient_to_detached

_KEYWORDS_SEPARATOR = ' '


class FoodType(enum.Enum):
    SOUP = 1
    MEAT = 2
    VEGAN = 3
    GRILL = 4
    PASTA_MEAT = 5
    PASTA_VEGAN = 6
    SALAD = 7
    SUB = 8


# TODO: Onboarding: User should get information on what each icon means
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


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    # Added for compat with datetime.date
    SATURDAY = 6
    SUNDAY = 7


class Campus(db.Model):
    __tablename__ = 'campus'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    short_name = db.Column(db.String(8), nullable=False)
    # TODO: Wouldn't it be easier to instead have a new table mapping keywords to campuses, resolving possible conflicts
    keywords = db.Column(db.Text(), default='', nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    page_url = db.Column(db.Text(), nullable=True)  # TODO: No campuses use this anymore in production, can be removed
    external_id = db.Column(db.Integer(), nullable=True)  # TODO: This can be made NOT NULL

    menus = db.relationship('Menu', backref='campus', passive_deletes=True)
    closing_days = db.relationship('ClosingDays', backref='campus', passive_deletes=True)
    subscriptions = db.relationship('UserSubscription', backref='campus', passive_deletes=True)

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
    def create(name: str, short_name: str, keywords: List[str], add_to_db=True) -> 'Campus':
        result = Campus(name, short_name)

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
    def get_all_active() -> 'List[Campus]':
        return Campus.query.filter_by(active=True).order_by(Campus.id).all()

    def __hash__(self):
        return hash(self.id)


class ClosingDays(db.Model):
    __tablename__ = 'closing_days'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    first_day = db.Column(db.Date(), nullable=False)
    last_day = db.Column(db.Date(), nullable=False)
    translatable_id = db.Column(db.Integer(), db.ForeignKey('translatable.id', onupdate='CASCADE', ondelete='RESTRICT'),
                                nullable=False)

    def __init__(self, campus_id: int, first_day: datetime.date, last_day: datetime.date,
                 translatable_id: int):
        if not isinstance(campus_id, int):
            raise ValueError('campus_id')
        if not isinstance(first_day, datetime.date):
            raise ValueError('first_day')
        if not isinstance(last_day, datetime.date):
            raise ValueError('last_day')
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')

        self.campus_id = campus_id
        self.first_day = first_day
        self.last_day = last_day
        self.translatable_id = translatable_id

    @staticmethod
    def create(campus: Campus, first_day: datetime.date, last_day: datetime.date, reason: str,
               language: str) -> 'ClosingDays':
        translatable, translation = Translatable.get_or_create(reason, language)

        result = ClosingDays(campus.id, first_day, last_day, translatable.id)

        db.session.add(result)

        return result

    @staticmethod
    def find_is_closed(campus: Campus, day: datetime.date) -> 'Optional[ClosingDays]':
        return ClosingDays.query.filter(db.and_(ClosingDays.campus_id == campus.id,
                                                ClosingDays.first_day <= day,
                                                ClosingDays.last_day >= day
                                                )).first()


class Translatable(db.Model):
    __tablename__ = 'translatable'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    original_language = db.Column(db.String(5), nullable=False)
    original_text = db.Column(db.String(256), nullable=False)

    translations = db.relationship('Translation', backref='translatable', passive_deletes=True)
    menu_items = db.relationship('MenuItem', backref='translatable')
    closing_days = db.relationship('ClosingDays', backref='translatable')

    def __init__(self, text: str, language: str):
        if not isinstance(text, str):
            raise ValueError('text')
        if not isinstance(language, str):
            raise ValueError('language')

        self.original_language = language
        self.original_text = text

    def add_translation(self, language: str, text: str) -> 'Translation':
        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is not None:
            return translation

        translation = Translation(self.id, language, text)

        if translation is not None:
            db.session.add(translation)

        return translation

    @staticmethod
    def get_or_create(text: str, language='nl_BE') -> 'Tuple[Translatable, Translation]':
        translatable = Translatable.query.filter_by(original_language=language, original_text=text).first()

        if translatable is not None:
            return translatable, Translation.query.filter_by(translatable_id=translatable.id, language=language).one()

        translatable = Translatable(text, language)
        db.session.add(translatable)
        db.session.flush()

        translation = Translation(translatable.id, language, text)
        db.session.add(translation)

        return translatable, translation

    @staticmethod
    def get_by_id(translatable_id) -> 'Optional[Translatable]':
        return Translatable.query.filter_by(id=translatable_id).first()

    def get_translation(self, language: str, translator: 'Callable[[str, str, str], str]') -> 'Translation':
        if not language:
            raise ValueError()

        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is None:
            original = Translation.query.filter_by(translatable_id=self.id, language=self.original_language).one()

            translation = self.add_translation(language, translator(original.translation, original.language, language))

        return translation

    def __hash__(self):
        return hash(self.id)


class Translation(db.Model):
    __tablename__ = 'translation'

    translatable_id = db.Column(db.Integer(), db.ForeignKey('translatable.id', onupdate='CASCADE', ondelete='CASCADE'),
                                primary_key=True)
    language = db.Column(db.String(5), primary_key=True)
    translation = db.Column(db.String(256), nullable=False)

    def __init__(self, translatable_id: int, language: str, translation: str):
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')
        if not isinstance(language, str):
            raise ValueError('language')
        if not isinstance(translation, str):
            raise ValueError('translation')

        self.translatable_id = translatable_id
        self.language = language
        self.translation = translation

    def __hash__(self):
        return hash((self.translatable_id, self.language))


class Menu(db.Model):
    __tablename__ = 'menu'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    menu_day = db.Column(db.Date(), nullable=False)

    menu_items = db.relationship('MenuItem', backref='menu', passive_deletes=True, order_by='MenuItem.food_type')

    def __init__(self, campus_id: int, day: datetime.date):
        if not isinstance(campus_id, int):
            raise ValueError('campus_id')
        if not isinstance(day, datetime.date):
            raise ValueError('day')

        self.campus_id = campus_id
        self.menu_day = day

    @staticmethod
    def create(campus: Campus, day: datetime.date, add_to_db=True):
        menu = Menu(campus.id, day)

        if add_to_db:
            db.session.add(menu)

        return menu

    def delete(self):
        db.session.delete(self)

    def update(self, new_menu: 'Menu'):
        old = self.menu_items  # type: List[MenuItem]
        new = new_menu.menu_items  # type: List[MenuItem]

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

    @staticmethod
    def get_menu(campus: Campus, day: datetime.date) -> 'Optional[Menu]':
        return Menu.query.filter_by(campus_id=campus.id, menu_day=day).first()

    def add_menu_item(self, translatable: Translatable, food_type: FoodType, price_students: Decimal,
                      price_staff: Optional[Decimal]):
        menu_item = MenuItem(self.id, translatable.id, food_type, price_students, price_staff)

        # FIXME: Is this safe?
        self.menu_items.append(menu_item)

        return menu_item

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
    price_students = db.Column(db.Numeric(4, 2), nullable=False)
    price_staff = db.Column(db.Numeric(4, 2), nullable=True)

    def __init__(self, menu_id: int, translatable_id: int, food_type: FoodType, price_students: Decimal,
                 price_staff: Optional[Decimal]):
        if menu_id is not None and not isinstance(menu_id, int):  # FIXME: Allowing a null ID is a dirty hack
            raise ValueError('menu_id')
        if not isinstance(translatable_id, int):
            raise ValueError('translatable_id')
        if not isinstance(food_type, FoodType):
            raise ValueError('food_type')
        if not isinstance(price_students, Decimal):
            raise ValueError('price_students')
        if price_staff is not None and not isinstance(price_staff, Decimal):
            raise ValueError('price_staff')

        self.menu_id = menu_id
        self.translatable_id = translatable_id
        self.food_type = food_type
        self.price_students = price_students
        self.price_staff = price_staff

    def copy(self, menu: Menu):
        return MenuItem(menu.id, self.translatable_id, self.food_type, self.price_students, self.price_staff)

    def get_translation(self, language: str, translator: 'Callable[[str, str, str], str]') -> 'Translation':
        return self.translatable.get_translation(language, translator)

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other: 'MenuItem') -> bool:
        if self.food_type == other.food_type:
            if self.translatable_id == other.translatable_id:
                return self.id < other.id
            return self.translatable_id < other.translatable_id
        return self.food_type < other.food_type

    def __eq__(self, other: 'MenuItem') -> bool:
        if self is other or (self.id is not None and self.id == other.id):
            return True
        # menu_id is ignored
        if self.translatable_id != other.translatable_id:
            return False
        if self.food_type != other.food_type:
            return False
        if self.price_students != other.price_students:
            return False
        if self.price_staff != other.price_staff:
            return False
        return True

    @staticmethod
    def format_price(price: Decimal) -> str:
        if price == 0.0:
            return ''
        return locale.currency(price).replace(' ', '')


class UserSubscription(db.Model):
    __tablename__ = 'user_subscription'

    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    day = db.Column(db.Enum(Day), primary_key=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id', onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False)
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
    def get_for_user(user: 'AppUser', day: Day) -> 'Optional[UserSubscription]':
        return UserSubscription.query.filter_by(user_id=user.id, day=day).first()

    @staticmethod
    def create(user: 'AppUser', day: Day, campus: Campus, active=True) -> 'Optional[UserSubscription]':
        # TODO: Prevent weekend days from actually being used here

        subscription = UserSubscription(user.id, day, campus.id, active)

        db.session.add(subscription)

        return subscription


class AppUser(db.Model):
    __tablename__ = 'app_user'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    provider = db.Column(db.String(32), nullable=False)  # String ID of the provider
    internal_id = db.Column(db.String(32), nullable=False)  # ID that is specific to the provider
    language = db.Column(db.String(5), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('provider', 'internal_id'),
    )

    subscriptions = db.relationship('UserSubscription', backref='user', passive_deletes=True)
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
        sub = UserSubscription.get_for_user(self, day)
        if sub is None:
            UserSubscription.create(self, day, campus, active=True if active is None else active)
        else:
            sub.campus = campus
            if active is not None:
                sub.active = active

    def get_campus(self, day: Day) -> 'Optional[Campus]':
        sub = UserSubscription.get_for_user(self, day)
        if sub is not None:
            return sub.campus
        else:
            return None

    def get_subscription(self, day: Day) -> 'Optional[UserSubscription]':
        return UserSubscription.get_for_user(self, day)

    def set_language(self, language: str):
        self.language = language

    def set_active(self, day: Day, active: bool):
        sub = UserSubscription.get_for_user(self, day)
        if sub is None:
            raise ValueError('User does not have a subscription on day {}'.format(day.name))

        sub.active = active

    @staticmethod
    def create(provider: str, internal_id: str, language: str):
        user = AppUser(provider, internal_id, language)

        db.session.add(user)

        return user

    @staticmethod
    def find_subscribed_users_by_day(day: Day, provider=None) -> 'List[AppUser]':
        q = AppUser.query
        if provider:
            q = q.filter_by(provider=provider)

        return q.join(AppUser.subscriptions).filter(db.and_(UserSubscription.day == day,
                                                            UserSubscription.active == True
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
    def find_by_id(string_id: str) -> 'Optional[Feature]':
        return Feature.query.filter_by(string_id=string_id).first()

    @staticmethod
    def get_all() -> 'List[Feature]':
        return Feature.query.all()

    @staticmethod
    def create(string_id: str, description: str = None, globally_available=False) -> 'Optional[Feature]':
        feature = Feature(string_id, description, globally_available)

        db.session.add(feature)

        return feature

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
    def get_for_user(user: AppUser, feature: Feature) -> 'Optional[FeatureParticipation]':
        return FeatureParticipation.query.filter_by(user_id=user.id, feature_id=feature.id).first()

    @staticmethod
    def create(user: AppUser, feature: Feature) -> 'Optional[FeatureParticipation]':
        participation = FeatureParticipation(user.id, feature.id)

        db.session.add(participation)

        return participation


def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def create_standard_values():
    cst = Campus.create('Stadscampus', 'cst', [])
    cst.external_id = 1
    cde = Campus.create('Campus Drie Eiken', 'cde', [])
    cde.external_id = 2
    cmi = Campus.create('Campus Middelheim', 'cmi', [])
    cmi.external_id = 3
    db.session.commit()


def import_dump(dump_file):
    campus_dict = dict()  # type: Dict[str, Campus]

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
