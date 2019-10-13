import datetime, enum
from typing import Callable, Dict, List, Optional, Tuple

from extensions import db


class FoodType(enum.Enum):
    SOUP = 1
    MEAT = 2
    VEGAN = 3
    GRILL = 4
    PASTA_MEAT = 5
    PASTA_VEGAN = 6


food_type_icons = {
    FoodType.SOUP: '🍵',
    FoodType.MEAT: '🍗',
    FoodType.VEGAN: '🍅',
    FoodType.GRILL: '🍖',
    FoodType.PASTA_MEAT: '🍝',
    FoodType.PASTA_VEGAN: '🍝',
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
    def create(name: str, short_name: str, keywords: List[str], page_url: str, commit=True):
        result = Campus(name, short_name)

        for keyword in keywords:
            result.add_keyword(keyword)

        result.add_keyword(short_name)

        result.set_page_url(page_url)

        db.session.add(result)

        if commit:
            db.session.commit()

        return result

    @staticmethod
    def get_by_short_name(short_name: str) -> 'Optional[Campus]':
        return Campus.query.filter_by(short_name=short_name).first()

    @staticmethod
    def get_by_id(id: int) -> 'Optional[Campus]':
        return Campus.query.filter_by(id=id).first()

    @staticmethod
    def get_active() -> 'List[Campus]':
        return Campus.query.filter_by(active=True).all()

    def __hash__(self):
        return hash(self.id)


# TODO: Probably some way of storing when a restaurant is closed (holidays, vacation, etc.)


class Translatable(db.Model):
    __tablename__ = 'translatable'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    original_language = db.Column(db.String(5), nullable=False)
    original_text = db.Column(db.String(256), nullable=False)

    translations = db.relationship('Translation', backref='translatable', passive_deletes=True)
    menu_items = db.relationship('MenuItem', backref='translatable')

    def __init__(self, text: str, language: str):
        self.original_language = language
        self.original_text = text

    def add_translation(self, language: str, text: str, commit=True) -> 'Translation':
        translation = Translation.query.filter_by(translatable_id=self.id, language=language).first()

        if translation is not None:
            return translation

        translation = Translation(self, language, text)

        if translation is not None:
            db.session.add(translation)

            if commit:
                db.session.commit()

        return translation

    @staticmethod
    def get_or_create(text: str, language='nl_BE', commit=True) -> 'Tuple[Translatable, Translation]':
        translatable = Translatable.query.filter_by(original_language=language, original_text=text).first()

        if translatable is not None:
            return translatable, Translation.query.filter_by(translatable_id=translatable.id, language=language).one()

        translatable = Translatable(text, language)
        db.session.add(translatable)

        translation = Translation(translatable, language, text)
        db.session.add(translation)

        if commit:
            db.session.commit()

        return translatable, translation

    @staticmethod
    def get_by_id(translatable_id) -> 'Optional[Translatable]':
        return Translatable.query.filter_by(id=translatable_id).first()

    def get_translation(self, language: str, translator: 'Callable[[str, str, str], str]') -> 'Translatable':
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

    menu_items = db.relationship('MenuItem', backref='menu', passive_deletes=True)

    def __init__(self, campus: Campus, day: datetime.date):
        self.campus = campus
        self.menu_day = day

    @staticmethod
    def create(campus: Campus, day: datetime.date, commit=True):
        menu = Menu(campus, day)
        db.session.add(menu)

        if commit:
            db.session.commit()

        return menu

    def delete(self, commit=True):
        db.session.delete(self)

        if commit:
            db.session.commit()

    @staticmethod
    def get_menu(campus: Campus, day: datetime.date) -> 'Optional[Menu]':
        return Menu.query.filter_by(campus_id=campus.id, menu_day=day).first()

    def add_menu_item(self, translatable: Translatable, food_type: FoodType, price_students: str, price_staff: str,
                      commit=True):
        menu_item = MenuItem(self, translatable, food_type, price_students, price_staff)
        db.session.add(menu_item)

        if commit:
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


class Subscription(db.Model):
    __tablename__ = 'subscription'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    # TODO: Subscriptions should probably reference to an internal user id
    # TODO: (could potentially allow for linking users to multiple origins, but that brings a whole lot of issues)
    # TODO: OR the facebook ID data is generified (though collisions could then happen?)
    provider = db.Column(db.String(32), nullable=False)  # String ID of the provider
    internal_id = db.Column(db.String(32), nullable=False)  # ID that is specific to the provider
    # facebook_id = db.Column(db.String(32), nullable=False, unique=True)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('provider', 'internal_id'),
    )

    language = db.Column(db.String(5), nullable=False)
    campus_mon_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    campus_tue_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    campus_wed_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    campus_thu_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    campus_fri_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)

    campus_mon = db.relationship('Campus', foreign_keys=[campus_mon_id])
    campus_tue = db.relationship('Campus', foreign_keys=[campus_tue_id])
    campus_wed = db.relationship('Campus', foreign_keys=[campus_wed_id])
    campus_thu = db.relationship('Campus', foreign_keys=[campus_thu_id])
    campus_fri = db.relationship('Campus', foreign_keys=[campus_fri_id])

    def __init__(self, facebook_id: str, language: str, campus: Optional[Campus]):
        self.facebook_id = facebook_id
        self.language = language
        if campus is not None:
            self.campus_mon = campus
            self.campus_tue = campus
            self.campus_wed = campus
            self.campus_thu = campus
            self.campus_fri = campus

    def set_campus(self, day: Day, campus: Campus):
        if day == Day.MONDAY:
            self.campus_mon = campus
        elif day == Day.TUESDAY:
            self.campus_tue = campus
        elif day == Day.WEDNESDAY:
            self.campus_wed = campus
        elif day == Day.THURSDAY:
            self.campus_thu = campus
        elif day == Day.FRIDAY:
            self.campus_fri = campus

    def get_campus(self, day: Day) -> 'Optional[Campus]':
        if day == Day.MONDAY:
            return self.campus_mon
        elif day == Day.TUESDAY:
            return self.campus_tue
        elif day == Day.WEDNESDAY:
            return self.campus_wed
        elif day == Day.THURSDAY:
            return self.campus_thu
        elif day == Day.FRIDAY:
            return self.campus_fri
        return None

    def set_language(self, language: str):
        self.language = language

    def set_active(self, active: bool):
        self.active = active

    # FIXME: Use provider
    @staticmethod
    def find_active(provider=None) -> 'List[Subscription]':
        return Subscription.query.filter_by(active=True).all()

    # FIXME
    @staticmethod
    def find_by_facebook_id(facebook_id: str) -> 'Optional[Subscription]':
        return Subscription.query.filter_by(facebook_id=facebook_id).first()

    def __hash__(self):
        return hash(self.id)


def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def create_standard_values():
    Campus.create('Stadscampus', 'cst', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/stadscampus/',
                  commit=False)
    Campus.create('Campus Drie Eiken', 'cde', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/campus-drie-eiken/',
                  commit=False)
    Campus.create('Campus Middelheim', 'cmi', [], 'https://www.uantwerpen.be/nl/studentenleven/eten/campus-middelheim/',
                  commit=False)
    db.session.commit()


def import_dump(dump_file):
    campus_dict = dict()  # type: Dict[str, Campus]

    def get_campus(short_name) -> Campus:
        if short_name not in campus_dict:
            campus_dict[short_name] = Campus.get_by_short_name(short_name)
        return campus_dict[short_name]

    with open(dump_file) as file:
        header = file.readline()

        line = file.readline()
        while line:
            line = line.strip()
            split = list(line.split('\t'))

            if len(split) == 8:
                split[1] = split[1] == 'True'
            if split[7] == '0':
                split[7] = ''  # Query locale

            sub = Subscription(split[0], split[7], None)
            sub.set_active(split[1])
            sub.set_campus(Day.MONDAY, get_campus(split[2]))
            sub.set_campus(Day.TUESDAY, get_campus(split[3]))
            sub.set_campus(Day.WEDNESDAY, get_campus(split[4]))
            sub.set_campus(Day.THURSDAY, get_campus(split[5]))
            sub.set_campus(Day.FRIDAY, get_campus(split[6]))

            db.session.add(sub)

            line = file.readline()

        db.session.commit()
