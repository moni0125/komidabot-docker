class Trigger:
    pass


class Message:
    def __init__(self, trigger: Trigger):
        self.trigger = trigger


class TextMessage(Message):
    def __init__(self, trigger: Trigger, text: str):
        super().__init__(trigger)
        self.text = text


class ConfigurationMessage(Message):
    def __init__(self, trigger: Trigger, options):
        super().__init__(trigger)
        self.options = options  # FIXME: Define a type for this


class MessageHandler:
    def send_message(self, user, message: 'Message'):
        raise NotImplementedError()
