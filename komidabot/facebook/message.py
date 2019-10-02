TYPE_REPLY = 'RESPONSE'
TYPE_SUBSCRIPTION = 'NON_PROMOTIONAL_SUBSCRIPTION'


class Message:
    def __init__(self, recipient: str, is_reply: bool):
        self.recipient = recipient
        self.is_reply = is_reply

    def get_data(self):
        return {
            'recipient': {
                'id': self.recipient
            },
            'message': {},
            'messaging_type': TYPE_REPLY if self.is_reply else TYPE_SUBSCRIPTION
        }


class TextMessage(Message):
    def __init__(self, recipient: str, is_reply: bool, text: str):
        super().__init__(recipient, is_reply)
        self.text = text

    def get_data(self):
        result = super().get_data()
        result['message'] = {
            'text': self.text
        }
        return result
