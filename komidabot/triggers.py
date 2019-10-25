import datetime
from typing import List

from komidabot.messages import Trigger
import komidabot.users as users


class NLPAttribute:
    def __init__(self, attribute: str, confidence: float, data: dict):
        self.attribute = attribute
        self.confidence = confidence
        self.data = data

    def __repr__(self):
        return 'NLPAttribute({}, {}, {})'.format(repr(self.attribute), repr(self.confidence), repr(self.data))


class SubscriptionTrigger(Trigger):
    def __init__(self, date: datetime.date = None):
        Trigger.__init__(self)
        self.date = date


class TextTrigger(Trigger):
    def __init__(self, text):
        Trigger.__init__(self)
        self.text = text


class AnnotatedTextTrigger(TextTrigger):
    def __init__(self, text, nlp_attributes=None):
        TextTrigger.__init__(self, text)
        self.nlp_attributes = nlp_attributes or []  # type: List[NLPAttribute]

    def add_attribute(self, attribute: NLPAttribute):
        self.nlp_attributes.append(attribute)

    def get_attributes(self, attribute: str):
        return [attr for attr in self.nlp_attributes if attr.attribute == attribute]


class UserTrigger(Trigger):
    def __init__(self, sender: users.User):
        Trigger.__init__(self)
        self.sender = sender


class UserTextTrigger(TextTrigger, UserTrigger):
    def __init__(self, text, sender):
        TextTrigger.__init__(self, text)
        UserTrigger.__init__(self, sender)


class AnnotatedUserTextTrigger(AnnotatedTextTrigger, UserTextTrigger, UserTrigger):
    def __init__(self, text, sender, nlp_attributes=None):
        AnnotatedTextTrigger.__init__(self, text, nlp_attributes=nlp_attributes)
        UserTrigger.__init__(self, sender)


# Facebook: postback payload
# Discord: !commands or using reactions?
class UserCustomTrigger(UserTrigger):
    pass


class AdminActionTrigger(Trigger):
    def __init__(self, sub_trigger: Trigger):
        self.sub_trigger = sub_trigger
