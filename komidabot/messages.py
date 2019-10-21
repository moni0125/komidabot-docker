class Trigger:
    pass


class Message:
    def __init__(self, trigger: Trigger):
        self.trigger = trigger


class TextMessage(Message):
    def __init__(self, trigger: Trigger, text: str):
        super().__init__(trigger)
        self.text = text


class MessageHandler:
    def send_message(self, user, message: 'Message'):
        raise NotImplementedError()
