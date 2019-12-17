import random

from typing import Callable


def localisation_definition(name, obj, fallback='en') -> Callable[[str], str]:
    for key, value in obj.copy().items():
        if isinstance(key, tuple):
            del obj[key]
            for k in key:
                obj[k] = value

    def wrapper(locale):
        if locale is None:
            result = obj[fallback]
        else:
            locale = locale.lower().split('_', 1)[0]
            result = obj[locale] if locale in obj else obj[fallback]

        if callable(result):
            return result()
        elif isinstance(result, list):
            weights, strings = zip(*result)
            return random.choices(strings, weights=weights)
        else:
            return result

    wrapper.__name__ = name

    return wrapper


# Supported locales:
#   https://developers.facebook.com/docs/messenger-platform/messenger-profile/supported-locales

INTERNAL_ERROR = localisation_definition('INTERNAL_ERROR', {
    'en': 'An unexpected error occured while trying to perform your request',
    'nl': [
        (1, 'oepsie woepsie! de bot is stukkie wukkie! we sijn heul hard '
            'aan t werk om dit te make mss kan je beter self kijken  owo'),
        (99, 'Een onverwachte fout gebeurde tijdens het uitvoeren van uw verzoek'),
    ],
})

# INTERNAL_ERROR = localisation_definition('INTERNAL_ERROR', {
#     'en': 'An unexpected error occured while trying to perform your request',
#     'nl': 'Een onverwachte fout gebeurde tijdens het uitvoeren van uw verzoek',
# })

ERROR_TEXT_ONLY = localisation_definition('ERROR_TEXT_ONLY', {
    'en': 'Sorry, I only understand text messages',
    'nl': 'Sorry, ik begrijp alleen tekstberichten',
})

ERROR_NOT_IMPLEMENTED = localisation_definition('ERROR_NOT_IMPLEMENTED', {
    'en': 'Sorry, this feature is currently not implemented',
    'nl': 'Sorry, deze feature is momenteel niet geïmplementeerd',
})

ERROR_POSTBACK = localisation_definition('ERROR_POSTBACK', {
    'en': 'Sorry, I cannot handle that message right now. '
          'Please try sending a message using the textbox instead.',
    'nl': 'Sorry, ik kan dit bericht momenteel niet begrijpen. '
          'Gelieve het tekstvak te gebruiken voor uw vraag.',
})

REPLY_NO_MENU = localisation_definition('REPLY_NO_MENU', {
    'en': 'Sorry, no menu is available for {campus} on {date}',
    'nl': 'Sorry, er is geen menu beschikbaar voor {campus} op {date}',
})

REPLY_CAMPUS_INACTIVE = localisation_definition('REPLY_CAMPUS_INACTIVE', {
    'en': 'Sorry, no menus are available for {campus}',
    'nl': 'Sorry, er zijn geen menus beschikbaar voor {campus}',
})

REPLY_WEEKEND = localisation_definition('REPLY_WEEKEND', {
    'en': 'Sorry, there are no menus on Saturdays and Sundays',
    'nl': 'Sorry, er zijn geen menus op zon- en zaterdagen',
})

REPLY_TOO_MANY_DAYS = localisation_definition('REPLY_TOO_MANY_DAYS', {
    'en': 'Sorry, please request only a single day',
    'nl': 'Sorry, gelieve een enkele dag te specificeren',
})

REPLY_INVALID_DATE = localisation_definition('REPLY_INVALID_DATE', {
    'en': 'Sorry, I am unable to understand the requested day. '
          'Please try to specify the day as e.g. "Monday" or "Tomorrow"',
    'nl': 'Sorry, ik kan de gevraagde dag niet begrijpen. '
          'Gelieve de dag aan te geven als bvb. "Maandag" of "Morgen"',
})

REPLY_TOO_MANY_CAMPUSES = localisation_definition('REPLY_TOO_MANY_CAMPUSES', {
    'en': 'Sorry, please only ask for a single campus at a time',
    'nl': 'Sorry, gelieve een enkele campus te specificeren',
})

REPLY_MENU_START = localisation_definition('REPLY_MENU_START', {
    'en': 'Menu at {campus} on {date}',
    'nl': 'Menu van {date} in {campus}',
})

REPLY_MENU_INCOMPLETE = localisation_definition('REPLY_MENU_START', {
    'en': '⚠️ NOTE: This menu may be incomplete',
    'nl': '⚠️ LET OP: Dit menu is mogelijks incompleet',
})

REPLY_USE_AT_ADMIN = localisation_definition('REPLY_USE_AT_ADMIN', {
    'en': "If you would like to talk to the admin instead, use @admin in your message and "
          "I won't disturb you\n~ 🤖 Komidabot",
    'nl': 'Als je met de admin wilt praten, dan kan je @admin gebruiken en '
          'zal ik je niet storen\n~ 🤖 Komidabot',
})

REPLY_NEW_USER = localisation_definition('REPLY_NEW_USER', {
    'en': 'Welcome to the Komidabot!',
    'nl': 'Welkom bij de Komidabot!',
})

REPLY_INSTRUCTIONS = localisation_definition('REPLY_INSTRUCTIONS', {
    'en': 'You can request the menu by choosing a campus ({campuses}) and/or '
          'asking for a specific day (Monday - Friday, Today, Tomorrow, etc.)\n\n'
          'To reach the admin, you can use @admin.',
    'nl': 'Je kan het menu opvragen door een campus te kiezen ({campuses}) en/of '
          'een specifieke dag te vragen (maandag - vrijdag, vandaag, morgen, etc.)\n\n'
          'Om de admin te bereiken, kan je @admin gebruiken.',
})

DOWN_FOR_MAINTENANCE = localisation_definition('DOWN_FOR_MAINTENANCE', {
    'en': 'I am temporarily down for maintenance, please check back later',
    'nl': 'Wegens onderhoud ben ik tijdelijk onbeschikbaar, probeer het later nog eens',
})

DAYS = [
    localisation_definition('DAYS[0]', {
        'en': 'Monday',
        'nl': 'maandag',
    }),
    localisation_definition('DAYS[1]', {
        'en': 'Tuesday',
        'nl': 'dinsdag',
    }),
    localisation_definition('DAYS[2]', {
        'en': 'Wednesday',
        'nl': 'woensdag',
    }),
    localisation_definition('DAYS[3]', {
        'en': 'Thursday',
        'nl': 'donderdag',
    }),
    localisation_definition('DAYS[4]', {
        'en': 'Friday',
        'nl': 'vrijdag',
    }),
    localisation_definition('DAYS[5]', {
        'en': 'Saturday',
        'nl': 'zaterdag',
    }),
    localisation_definition('DAYS[6]', {
        'en': 'Sunday',
        'nl': 'zondag',
    }),
]

MONTHS = [
    localisation_definition('MONTHS[0]', {'en': 'January', 'nl': 'januari', }),
    localisation_definition('MONTHS[1]', {'en': 'February', 'nl': 'februari', }),
    localisation_definition('MONTHS[2]', {'en': 'March', 'nl': 'maart', }),
    localisation_definition('MONTHS[3]', {'en': 'April', 'nl': 'april', }),
    localisation_definition('MONTHS[4]', {'en': 'May', 'nl': 'mei', }),
    localisation_definition('MONTHS[5]', {'en': 'June', 'nl': 'Juni', }),
    localisation_definition('MONTHS[6]', {'en': 'July', 'nl': 'juli', }),
    localisation_definition('MONTHS[7]', {'en': 'August', 'nl': 'augustus', }),
    localisation_definition('MONTHS[8]', {'en': 'September', 'nl': 'september', }),
    localisation_definition('MONTHS[9]', {'en': 'October', 'nl': 'october', }),
    localisation_definition('MONTHS[10]', {'en': 'November', 'nl': 'november', }),
    localisation_definition('MONTHS[11]', {'en': 'December', 'nl': 'december', }),
]

CONTINUATION = localisation_definition('CONTINUATION', {
    'en': ' (cont.)',
    'nl': ' (vervolg)',
})

SELECTED = localisation_definition('SELECTED', {
    'en': ' (current)',
    'nl': ' (geselecteerd)',
})

UNSUBSCRIBE = localisation_definition('UNSUBSCRIBE', {
    'en': 'Unsubscribe',
    'nl': 'Uitschrijven',
})

UNSUBSCRIBED = localisation_definition('UNSUBSCRIBED', {
    'en': 'Unsubscribed',
    'nl': 'Uitgeschreven',
})

REPLY_EXPERIMENTAL_DISPLAY = localisation_definition('REPLY_EXPERIMENTAL_DISPLAY', {
    'en': 'This feature display is experimental and will change in the future.',
    'nl': 'De weergave van deze feature is experimenteel en zal veranderen in de toekomst.',
})

REPLY_FEATURE_UNAVAILABLE = localisation_definition('REPLY_FEATURE_UNAVAILABLE', {
    'en': 'This feature is currently unavailable.',
    'nl': 'Deze feature is momenteel niet beschikbaar.',
})

REPLY_SET_SUBSCRIPTION = localisation_definition('REPLY_SET_SUBSCRIPTION', {
    'en': 'Preference for {day} set to: {campus}',
    'nl': 'Voorkeur voor {day} gezet op: {campus}',
})

REPLY_SET_LANGUAGE = localisation_definition('REPLY_SET_SUBSCRIPTION', {
    'en': 'Your language is now set to: {language}',
    'nl': 'Uw taal staat nu op: {language}',
})

MESSAGE_NO_SUBSCRIPTIONS = localisation_definition('REPLY_SET_SUBSCRIPTION', {
    'en': 'Dear user, from now on you can once again request the bot to send a daily menu at 10am.\n\n'
          'You can set this up by clicking on the "Manage subscription" button in the menu.\n\n'
          'Your preferences for this are per-day and can be changed at any moment.',
    'nl': 'Beste gebruiker, vanaf nu kan je de bot terug vragen om dagelijks het menu naar je te sturen.\n\n'
          'Je kan dit instellen door in het menu op "Manage subscription" te drukken.\n\n'
          'Uw voorkeuren hiervoor zijn per dag en kunnen op ieder moment aangepast worden.',
})

MESSAGE_FIRST_SUBSCRIPTION = localisation_definition('REPLY_SET_SUBSCRIPTION', {
    'en': 'Dear user, from now on the bot will send you the daily menu at 10am once again.\n\n'
          'You can change your preferences by clicking on the "Manage subscription" button in the menu.\n\n'
          'Your preferences are per-day and can be changed at any moment.',
    'nl': 'Beste gebruiker, vanaf nu zal de bot terug automatisch het menu doorsturen om 10 uur.\n\n'
          'Je kan je voorkeuren aanpassen door in het menu op "Manage subscription" te drukken.\n\n'
          'Uw voorkeuren zijn per dag en kunnen op ieder moment aangepast worden.',
})
