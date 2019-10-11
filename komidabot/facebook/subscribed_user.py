from komidabot.facebook.message import TextMessage
from komidabot.facebook.user_legacy import User


# TODO: Deprecated
class SubscribedUser(User):
    def __init__(self, sender: str):
        super().__init__(sender)

    def send_text_message(self, message: str):
        return self.send_message(TextMessage(self.user_id, False, message))

    def get_locale(self):
        return super().get_locale()

    def update_locale(self):
        pass

    def __repr__(self):
        return 'SubscribedUser({})'.format(repr(self.user_id))
