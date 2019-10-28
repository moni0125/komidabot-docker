import datetime
from typing import Optional

from komidabot.models import Campus, Menu, MenuItem, Translatable, Translation, food_type_icons

# TODO: Translations DEFINITELY need to be moved out of this file
from googletrans import Translator

translator = Translator()


def translate_item(text: str, original_language: str, translated_language: str):
    return translator.translate(text, src=original_language, dest=translated_language).text


def get_translated_text(translatable: Translatable, locale: str) -> Translation:
    if locale == 'zh_CN' or locale == 'zh_SG':
        locale = 'zh-cn'
    elif locale == 'zh_HK' or locale == 'zh_TW':
        locale = 'zh-tw'
    elif not locale:
        locale = translatable.original_language

    return translatable.get_translation(locale, translate_item)


def prepare_menu_text(campus: Campus, day: datetime.date, locale: str) -> 'Optional[str]':
    menu = Menu.get_menu(campus, day)

    if menu is None:
        return None

    result = ['Menu at {} on {}'.format(campus.short_name.upper(), str(day)), '']

    try:
        for item in menu.menu_items:  # type: MenuItem
            translation = get_translated_text(item, locale)
            price_str = '{} / {}'.format(item.price_students, item.price_staff)
            if not item.price_staff:
                price_str = item.price_students
            result.append('{} {} ({})'.format(food_type_icons[item.food_type], translation.translation, price_str))
    except Exception:
        print('Failed translating to {}'.format(locale), flush=True)
        raise

    return '\n'.join(result)
