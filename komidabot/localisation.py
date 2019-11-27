import random


def localisation_definition(name, obj, fallback='en'):
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
