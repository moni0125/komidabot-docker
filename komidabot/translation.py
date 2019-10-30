from googletrans import Translator

import komidabot.models as models

translator = Translator()


def translate_item(text: str, original_language: str, translated_language: str):
    return translator.translate(text, src=original_language, dest=translated_language).text


def get_translated_text(translatable: models.Translatable, locale: str) -> models.Translation:
    if locale == 'zh_CN' or locale == 'zh_SG':
        locale = 'zh-cn'
    elif locale == 'zh_HK' or locale == 'zh_TW':
        locale = 'zh-tw'
    elif not locale:
        locale = translatable.original_language

    return translatable.get_translation(locale, translate_item)
