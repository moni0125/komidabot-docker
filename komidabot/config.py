from komidabot.models import AppSettings


def is_registrations_enabled():
    return AppSettings.get_value('registrations_enabled') is True
