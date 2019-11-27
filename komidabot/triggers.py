import datetime

import komidabot.users as users
from komidabot.messages import Aspect, Trigger


class SubscriptionTrigger(Trigger):
    def __init__(self, *args, date: datetime.date = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = date

    def get_repr_text(self):
        return ['SubscriptionTrigger', '- Date: ' + repr(self.date)]


class TextTrigger(Trigger):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def get_repr_text(self):
        return ['TextTrigger', '- Text: ' + repr(self.text)]


class NewUserAspect(Aspect):
    def __repr__(self):
        return 'NewUserAspect()'


class SenderAspect(Aspect):
    def __init__(self, sender: users.User):
        super().__init__()
        self.sender = sender

    def __repr__(self):
        return 'SenderAspect({})'.format(repr(self.sender))


class AtAdminAspect(Aspect):
    def __repr__(self):
        return 'AtAdminAspect()'


class DatetimeAspect(Aspect):
    allows_multiple = True

    def __init__(self, value: str, grain: str):
        super().__init__()
        self.value = value
        self.grain = grain

    def __repr__(self):
        return 'DatetimeAspect({}, {})'.format(repr(self.value), self.grain)


class LocaleAspect(Aspect):
    def __init__(self, locale: str, confidence: float):
        super().__init__()
        self.locale = locale
        self.confidence = confidence

    def __repr__(self):
        return 'LocaleAspect({}, {})'.format(self.locale, self.confidence)
