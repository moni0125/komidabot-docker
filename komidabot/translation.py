from googletrans import Translator

Language = str

LANGUAGE_DUTCH = 'nl'
LANGUAGE_ENGLISH = 'en'
LANGUAGE_FRENCH = 'fr'


def _fix_language(language: Language):
    if language == 'zh_CN' or language == 'zh_SG':
        return 'zh-cn'
    elif language == 'zh_HK' or language == 'zh_TW':
        return 'zh-tw'

    return language


class TranslationService:
    def translate(self, text: str, from_language: Language, to_language: Language):
        """
        Submit a string to be translated.
        :param text: The string to translate
        :param from_language: A 2 letter string defining the language to translate from
        :param to_language: A 2 letter string defining the language to translate to
        :return: The translated string
        """
        raise NotImplementedError()

    @property
    def identifier(self):
        raise NotImplementedError()

    @property
    def pretty_name(self):
        raise NotImplementedError()


class KomidaTranslationService(TranslationService):
    def translate(self, text: str, from_language: Language, to_language: Language):
        raise Exception('Komida translator service is a placeholder and cannot translate')

    @property
    def identifier(self):
        return 'komida'

    @property
    def pretty_name(self):
        return 'Komida'


class GoogleTranslationService(TranslationService):
    def __init__(self):
        self.translator = Translator()

    def translate(self, text: str, from_language: Language, to_language: Language):
        return self.translator.translate(text, src=from_language, dest=to_language).text

    @property
    def identifier(self):
        return 'google'

    @property
    def pretty_name(self):
        return 'Google Translate'


class BingTranslationService(TranslationService):
    def translate(self, text: str, from_language: Language, to_language: Language):
        raise NotImplementedError()

    @property
    def identifier(self):
        return 'bing'

    @property
    def pretty_name(self):
        return 'Bing Translate'
