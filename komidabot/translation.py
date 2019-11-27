from googletrans import Translator

Language = str


def _fix_language(language: Language):
    if language == 'zh_CN' or language == 'zh_SG':
        return 'zh-cn'
    elif language == 'zh_HK' or language == 'zh_TW':
        return 'zh-tw'

    return language


class TranslationService:
    def translate(self, text: str, from_language: Language, to_language: Language):
        raise NotImplementedError()

    @property
    def identifier(self):
        raise NotImplementedError()

    @property
    def pretty_name(self):
        raise NotImplementedError()


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
