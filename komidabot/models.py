import datetime, enum
from typing import Callable, Dict, List, Optional, Tuple

from extensions import db


# FIXME: Every query operation in this file should require a session object?


class FoodType(enum.Enum):
    SOUP = 1
    MEAT = 2
    VEGAN = 3
    GRILL = 4
    PASTA_MEAT = 5
    PASTA_VEGAN = 6
    SALAD = 7
    SUB = 8


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
    keywords = db.Column(db.Text(), default='', nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    page_url = db.Column(db.Text(), default='', nullable=False)

    menus = db.relationship('Menu', backref='campus', passive_deletes=True)
    closing_days = db.relationship('ClosingDays', backref='campus', passive_deletes=True)
    subscriptions = db.relationship('UserSubscription', backref='campus', passive_deletes=True)

    def __init__(self, name: str, short_name: str):
        self.name = name
        self.short_name = short_name
        self.keywords = ''

    def add_keyword(self, keyword: str):
        self.keywords = ' '.join(set(self.keywords.split() + [keyword, ]))

    def remove_keyword(self, keyword: str):
        self.keywords = ' '.join(set([kw for kw in self.keywords.split() if kw != keyword]))

    def set_active(self, active: bool):
        self.active = active

    def set_page_url(self, page_url):
        self.page_url = page_url

    @staticmethod
    def create(name: str, short_name: str, keywords: List[str], page_url: str, session=None):
        result = Campus(name, short_name)

        for keyword in keywords:
            result.add_keyword(keyword)

        result.add_keyword(short_name)

        result.set_page_url(page_url)

        if session is not None:
            session.add(result)
        else:
            db.session.add(result)
            db.session.commit()

        return result

    @staticmethod
    def get_by_short_name(short_name: str) -> 'Optional[Campus]':
        return Campus.query.filter_by(short_name=short_name).first()

    @staticmethod
    def get_by_id(campus_id: int) -> 'Optional[Campus]':
        return Campus.query.filter_by(id=campus_id).first()

    @staticmethod
    def get_active() -> 'List[Campus]':
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

    def __init__(self, campus: Campus, first_day: datetime.date, last_day: datetime.date, translatable: 'Translatable'):
        self.campus = campus
        self.first_day = first_day
        self.last_day = last_day
        self.translatable = translatable

    @staticmethod
    def create(campus: Campus, first_day: datetime.date, last_day: datetime.date, reason: str, language: str,
               session=None) -> 'ClosingDays':
        translatable, translation = Translatable.get_or_create(reason, language, session=session)

        result = ClosingDays(campus, first_day, last_day, translatable)

        if session is not None:
            session.add(result)
        else:
            db.session.add(result)
            db.session.commit()

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
        self.original_language = language
        self.original_text = text

    def add_translation(self, language: str, text: str, session=None) -> 'Translation':
        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is not None:
            return translation

        translation = Translation(self, language, text)

        if translation is not None:
            if session is not None:
                session.add(translation)
            else:
                db.session.add(translation)
                db.session.commit()

        return translation

    @staticmethod
    def get_or_create(text: str, language='nl_BE', session=None) -> 'Tuple[Translatable, Translation]':
        translatable = Translatable.query.filter_by(original_language=language, original_text=text).first()

        if translatable is not None:
            return translatable, Translation.query.filter_by(translatable_id=translatable.id, language=language).one()

        translatable = Translatable(text, language)
        translation = Translation(translatable, language, text)

        if session is not None:
            session.add(translatable)
            session.add(translation)
        else:
            db.session.add(translatable)
            db.session.add(translation)
            db.session.commit()

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

    def __init__(self, translatable: Translatable, language: str, translation: str):
        self.translatable = translatable
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

    def __init__(self, campus: Campus, day: datetime.date):
        self.campus = campus
        self.menu_day = day

    @staticmethod
    def create(campus: Campus, day: datetime.date, session=None):
        menu = Menu(campus, day)

        if session is not None:
            session.add(menu)
        else:
            db.session.add(menu)
            db.session.commit()

        return menu

    def delete(self, session=None):
        if session is not None:
            session.delete(self)
        else:
            db.session.delete(self)
            db.session.commit()

    @staticmethod
    def get_menu(campus: Campus, day: datetime.date) -> 'Optional[Menu]':
        return Menu.query.filter_by(campus_id=campus.id, menu_day=day).first()

    def add_menu_item(self, translatable: Translatable, food_type: FoodType, price_students: str, price_staff: str,
                      session=None):
        menu_item = MenuItem(self, translatable, food_type, price_students, price_staff)

        if session is not None:
            session.add(menu_item)
        else:
            db.session.add(menu_item)
            db.session.commit()

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
    price_students = db.Column(db.String(8), nullable=False)
    price_staff = db.Column(db.String(8), nullable=False)

    def __init__(self, menu: Menu, translatable: Translatable, food_type: FoodType, price_students: str,
                 price_staff: str):
        self.menu = menu
        self.translatable = translatable
        self.food_type = food_type
        self.price_students = price_students
        self.price_staff = price_staff

    def get_translation(self, language: str, translator: 'Callable[[str, str, str], str]') -> 'Translation':
        return self.translatable.get_translation(language, translator)

    def __hash__(self):
        return hash(self.id)


class UserSubscription(db.Model):
    __tablename__ = 'user_subscription'

    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    day = db.Column(db.Enum(Day), primary_key=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id', onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)  # FIXME: Deprecated

    def __init__(self, user: 'AppUser', day: Day, campus: Campus, active=True) -> None:
        self.user = user
        self.day = day
        self.campus = campus
        self.active = active

    @staticmethod
    def get_for_user(user: 'AppUser', day: Day) -> 'Optional[UserSubscription]':
        return UserSubscription.query.filter_by(user_id=user.id, day=day).first()

    @staticmethod
    def create(user: 'AppUser', day: Day, campus: Campus, active=True, session=None) -> 'Optional[UserSubscription]':
        # TODO: Prevent weekend days from actually being used here

        subscription = UserSubscription(user, day, campus, active)

        if session is not None:
            session.add(subscription)
        else:
            db.session.add(subscription)
            db.session.commit()

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
        self.provider = provider
        self.internal_id = internal_id
        self.language = language

    def set_campus(self, day: Day, campus: Campus, active=None, session=None):
        sub = UserSubscription.get_for_user(self, day)
        if sub is None:
            UserSubscription.create(self, day, campus, active=True if active is None else active, session=session)
        else:
            sub.campus = campus
            if active is not None:
                sub.active = active

            if session is None:
                db.session.commit()

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
    def create(provider: str, internal_id: str, language: str, session=None):
        user = AppUser(provider, internal_id, language)

        if session is not None:
            session.add(user)
        else:
            db.session.add(user)
            db.session.commit()

        return user

    @staticmethod
    def find_subscribed_users_by_day(day: Day, provider=None) -> 'List[AppUser]':
        q = AppUser.query
        if provider:
            q = q.filter_by(provider=provider)

        return q.join(AppUser.subscriptions).filter(db.and_(UserSubscription.day == day,
                                                            UserSubscription.active == True
                                                            )).order_by(AppUser.provider, AppUser.internal_id).all()

    # FIXME: Deprecated
    @staticmethod
    def find_by_facebook_id(facebook_id: str) -> 'Optional[AppUser]':
        return AppUser.query.filter_by(provider='facebook', internal_id=facebook_id).first()

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
    def create(string_id: str, description: str = None, globally_available=False, session=None) -> 'Optional[Feature]':
        feature = Feature(string_id, description, globally_available)

        if session is not None:
            session.add(feature)
        else:
            db.session.add(feature)
            db.session.commit()

        return feature

    @staticmethod
    def is_user_participating(user: AppUser, string_id: str) -> bool:
        if user is None:
            return False
        feature = Feature.find_by_id(string_id)
        if feature is None:
            return False

        if feature.globally_available:
            return True

        return FeatureParticipation.get_for_user(user, feature) is not None

    @staticmethod
    def set_user_participating(user: AppUser, string_id: str, participating: bool, session=None):
        feature = Feature.find_by_id(string_id)
        participation = FeatureParticipation.get_for_user(user, feature)

        if participating:
            if not participation:
                FeatureParticipation.create(user, feature, session=session)
        else:
            if participation:
                if session is not None:
                    session.delete(feature)
                else:
                    db.session.delete(feature)
                    db.session.commit()


class FeatureParticipation(db.Model):
    __tablename__ = 'feature_participation'

    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    feature_id = db.Column(db.Integer(), db.ForeignKey('feature.id', onupdate='CASCADE', ondelete='CASCADE'),
                           primary_key=True)

    def __init__(self, user: AppUser, feature: Feature):
        self.user = user
        self.feature = feature

    @staticmethod
    def get_for_user(user: AppUser, feature: Feature) -> 'Optional[FeatureParticipation]':
        return FeatureParticipation.query.filter_by(user_id=user.id, feature_id=feature.id).first()

    @staticmethod
    def create(user: AppUser, feature: Feature, session=None) -> 'Optional[FeatureParticipation]':
        participation = FeatureParticipation(user, feature)

        if session is not None:
            session.add(participation)
        else:
            db.session.add(participation)
            db.session.commit()

        return participation


def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def create_standard_values():
    session = db.session  # FIXME: Get session as a parameter
    Campus.create('Stadscampus', 'cst', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/stadscampus/',
                  session=session)
    Campus.create('Campus Drie Eiken', 'cde', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/campus-drie-eiken/',
                  session=session)
    Campus.create('Campus Middelheim', 'cmi', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/campus-middelheim/',
                  session=session)
    session.commit()


def import_dump(dump_file):
    campus_dict = dict()  # type: Dict[str, Campus]

    def get_campus(short_name) -> Campus:
        if short_name not in campus_dict:
            campus_dict[short_name] = Campus.get_by_short_name(short_name)
        return campus_dict[short_name]

    with open(dump_file) as file:
        _ = file.readline()  # Skip header

        session = db.session  # FIXME: Create new session

        line = file.readline()
        while line:
            line = line.strip()
            split = list(line.split('\t'))

            if len(split) == 8:
                split[1] = split[1] == 'True'
            if split[7] == '0':
                split[7] = ''  # Query locale

            user = AppUser.create('facebook', split[0], split[7])
            user.set_campus(Day.MONDAY, get_campus(split[2]), active=split[1], session=session)
            user.set_campus(Day.TUESDAY, get_campus(split[3]), active=split[1], session=session)
            user.set_campus(Day.WEDNESDAY, get_campus(split[4]), active=split[1], session=session)
            user.set_campus(Day.THURSDAY, get_campus(split[5]), active=split[1], session=session)
            user.set_campus(Day.FRIDAY, get_campus(split[6]), active=split[1], session=session)

            session.add(user)

            line = file.readline()

        session.commit()
