import datetime

import komidabot.users as users
from komidabot.messages import Aspect, Trigger


class SubscriptionTrigger(Trigger):
    def __init__(self, *args, date: datetime.date = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = date


class TextTrigger(Trigger):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text


class SenderAspect(Aspect):
    def __init__(self, sender: users.User):
        super().__init__()
        self.sender = sender


class DatetimeAspect(Aspect):
    allows_multiple = True

    def __init__(self, value: str, grain: str):
        super().__init__()
        self.value = value
        self.grain = grain


class LocaleAspect(Aspect):
    def __init__(self, locale: str):
        super().__init__()
        self.locale = locale
