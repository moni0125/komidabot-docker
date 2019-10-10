from typing import List

from komidabot.facebook.message_sender import MessageSender


class NLPAttribute:
    def __init__(self, attribute: str, confidence: float, data: dict):
        self.attribute = attribute
        self.confidence = confidence
        self.data = data

    def __repr__(self):
        return 'NLPAttribute({}, {}, {})'.format(repr(self.attribute), repr(self.confidence), repr(self.data))


class ReceivedMessage:
    def __init__(self, sender: MessageSender, nlp_attributes=None):
        if nlp_attributes is None:
            nlp_attributes = []
        self.sender = sender
        self.nlp_attributes = nlp_attributes  # type: List[NLPAttribute]

    def add_attribute(self, attribute: NLPAttribute):
        self.nlp_attributes.append(attribute)

    def get_attributes(self, attribute: str):
        return [attr for attr in self.nlp_attributes if attr.attribute == attribute]

    def __repr__(self):
        return 'ReceivedMessage({}, nlp_attributes={})'.format(repr(self.sender), repr(self.nlp_attributes))


class ReceivedTextMessage(ReceivedMessage):
    def __init__(self, sender: MessageSender, text: str, nlp_attributes=None):
        super().__init__(sender, nlp_attributes=nlp_attributes)
        self.text = text

    def __repr__(self):
        return 'ReceivedTextMessage({}, {}, nlp_attributes={})'.format(repr(self.sender), repr(self.text),
                                                                       repr(self.nlp_attributes))
