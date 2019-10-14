def localisation_definition(name, obj, fallback='en_US'):
    for key, value in obj.copy().items():
        if isinstance(key, tuple):
            del obj[key]
            for k in key:
                obj[k] = value

    def wrapper(locale):
        if locale is None:
            return obj[fallback]
        return obj[locale] if locale in obj else obj[fallback]

    wrapper.__name__ = name

    return wrapper


# Supported locales:
#   https://developers.facebook.com/docs/messenger-platform/messenger-profile/supported-locales

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

DOWN_FOR_MAINTENANCE1 = localisation_definition('ERROR_TEXT_ONLY', {
    ('en_US', 'en_GB'): 'I am temporarily down for maintenance, please check back later',
    ('nl_BE', 'nl_NL'): 'Wegens onderhoud ben ik tijdelijk onbeschikbaar, probeer het later nog eens',
})

DOWN_FOR_MAINTENANCE2 = localisation_definition('ERROR_TEXT_ONLY', {
    ('en_US', 'en_GB'): 'You can check the menu manually for now by going to '
                        'https://www.uantwerpen.be/nl/studentenleven/eten/',
    ('nl_BE', 'nl_NL'): 'U kunt het menu ook manueel bezien op het volgende adres: '
                        'https://www.uantwerpen.be/nl/studentenleven/eten/',
})
