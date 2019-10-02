from flask import current_app as app

from komidabot.facebook.message import TextMessage
from komidabot.facebook.user_legacy import User


class MessageSender(User):
    def __init__(self, user_id: str):
        super().__init__(user_id)

    def send_text_message(self, message: str):
        return self.send_message(TextMessage(self.user_id, True, message))

    def mark_seen(self):
        return app.messenger.mark_read(self)

    def __repr__(self):
        return 'MessageSender({})'.format(repr(self.user_id))
