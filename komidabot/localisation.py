import random


def localisation_definition(name, obj, fallback='en_US'):
    for key, value in obj.copy().items():
        if isinstance(key, tuple):
            del obj[key]
            for k in key:
                obj[k] = value

    def wrapper(locale):
        if locale is None:
            result = obj[fallback]
        else:
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
    ('en_US', 'en_GB'): '⚠️ An unexpected error occured while trying to perform your request',
    ('nl_BE', 'nl_NL'): [
        (1, 'oepsie woepsie! de bot is stukkie wukkie! we sijn heul hard '
            'aan t werk om dit te make mss kan je beter self kijken  owo'),
        (99, '⚠️ Een onverwachte fout gebeurde tijdens het uitvoeren van uw verzoek'),
    ],
})

# INTERNAL_ERROR = localisation_definition('INTERNAL_ERROR', {
#     ('en_US', 'en_GB'): 'An unexpected error occured while trying to perform your request',
#     ('nl_BE', 'nl_NL'): 'Een onverwachte fout gebeurde tijdens het uitvoeren van uw verzoek',
# })

ERROR_TEXT_ONLY = localisation_definition('ERROR_TEXT_ONLY', {
    ('en_US', 'en_GB'): 'Sorry, I only understand text messages',
    ('nl_BE', 'nl_NL'): 'Sorry, ik begrijp alleen tekstberichten',
})

ERROR_NOT_IMPLEMENTED = localisation_definition('ERROR_NOT_IMPLEMENTED', {
    ('en_US', 'en_GB'): 'Sorry, this feature is currently not implemented',
    ('nl_BE', 'nl_NL'): 'Sorry, deze feature is momenteel niet geïmplementeerd',
})

ERROR_POSTBACK = localisation_definition('ERROR_POSTBACK', {
    ('en_US', 'en_GB'): 'Sorry, I cannot handle that message right now. '
                        'Please try sending a message using the textbox instead.',
    ('nl_BE', 'nl_NL'): 'Sorry, ik kan dit bericht momenteel niet begrijpen. '
                        'Gelieve het tekstvak te gebruiken voor uw vraag.',
})

REPLY_NO_MENU = localisation_definition('REPLY_NO_MENU', {
    ('en_US', 'en_GB'): 'Sorry, no menu is available for {campus} on {date}',
    ('nl_BE', 'nl_NL'): 'Sorry, er is geen menu beschikbaar voor {campus} op {date}',
})

REPLY_WEEKEND = localisation_definition('REPLY_WEEKEND', {
    ('en_US', 'en_GB'): 'Sorry, there are no menus on Saturdays and Sundays',
    ('nl_BE', 'nl_NL'): 'Sorry, er zijn geen menus op zon- en zaterdagen',
})

REPLY_TOO_MANY_DAYS = localisation_definition('REPLY_TOO_MANY_DAYS', {
    ('en_US', 'en_GB'): 'Sorry, please request only a single day',
    ('nl_BE', 'nl_NL'): 'Sorry, gelieve een enkele dag te specificeren',
})

REPLY_INVALID_DATE = localisation_definition('REPLY_INVALID_DATE', {
    ('en_US', 'en_GB'): 'Sorry, I am unable to understand the requested day. '
                        'Please try to specify the day as e.g. "Monday" or "Tomorrow"',
    ('nl_BE', 'nl_NL'): 'Sorry, ik kan de gevraagde dag niet begrijpen. '
                        'Gelieve de dag aan te geven als bvb. "Maandag" of "Morgen"',
})

REPLY_TOO_MANY_CAMPUSES = localisation_definition('REPLY_TOO_MANY_CAMPUSES', {
    ('en_US', 'en_GB'): 'Sorry, please only ask for a single campus at a time',
    ('nl_BE', 'nl_NL'): 'Sorry, gelieve een enkele campus te specificeren',
})

REPLY_MENU_START = localisation_definition('REPLY_MENU_START', {
    ('en_US', 'en_GB'): 'Menu at {campus} on {date}',
    ('nl_BE', 'nl_NL'): 'Menu van {date} in {campus}',
})

REPLY_MENU_INCOMPLETE = localisation_definition('REPLY_MENU_START', {
    ('en_US', 'en_GB'): '⚠️ NOTE: This menu may be incomplete',
    ('nl_BE', 'nl_NL'): '⚠️ LET OP: Dit menu is mogelijks incompleet',
})

DOWN_FOR_MAINTENANCE1 = localisation_definition('ERROR_TEXT_ONLY', {
    ('en_US', 'en_GB'): '⚠️ I am temporarily down for maintenance, please check back later',
    ('nl_BE', 'nl_NL'): '⚠️ Wegens onderhoud ben ik tijdelijk onbeschikbaar, probeer het later nog eens',
})

DOWN_FOR_MAINTENANCE2 = localisation_definition('ERROR_TEXT_ONLY', {
    ('en_US', 'en_GB'): 'You can check the menu manually for now by going to '
                        'https://www.uantwerpen.be/nl/studentenleven/eten/',
    ('nl_BE', 'nl_NL'): 'U kunt het menu ook manueel bezien op het volgende adres: '
                        'https://www.uantwerpen.be/nl/studentenleven/eten/',
})
