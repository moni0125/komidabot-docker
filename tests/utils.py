import datetime

import komidabot.translation as translation

DAYS = {
    'MON': datetime.date(2019, 7, 1),
    'TUE': datetime.date(2019, 7, 2),
    'WED': datetime.date(2019, 7, 3),
    'THU': datetime.date(2019, 7, 4),
    'FRI': datetime.date(2019, 7, 5),
    'SAT': datetime.date(2019, 7, 6),
    'SUN': datetime.date(2019, 7, 7),
}

DAYS_LIST = list(DAYS.values())


class StubTranslator(translation.TranslationService):
    def translate(self, text: str, from_language: translation.Language, to_language: translation.Language):
        return 'No translation {}: {} -> {}'.format(repr(text), from_language, to_language)

    @property
    def identifier(self):
        return 'stub'

    @property
    def pretty_name(self):
        return 'Stub translator implementation'
