# TODO: Deprecated
class Message:
    def __init__(self, recipient: str):
        self.recipient = recipient


# TODO: Deprecated
class TextMessage(Message):
    def __init__(self, recipient: str, text: str):
        super().__init__(recipient)
        self.text = text
