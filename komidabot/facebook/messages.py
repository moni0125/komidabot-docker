import komidabot.facebook.constants as fb_constants
import komidabot.messages as messages
import komidabot.triggers as triggers
import komidabot.users as users
from komidabot.app import get_app

TYPE_REPLY = 'RESPONSE'
TYPE_SUBSCRIPTION = 'NON_PROMOTIONAL_SUBSCRIPTION'


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message):
        if user.id.provider != fb_constants.PROVIDER_ID:
            raise ValueError('User id is not for Facebook')

        if isinstance(message, messages.TextMessage):
            self._send_text_message(user.id, message)
        elif isinstance(message, TemplateMessage):
            self._send_template_message(user.id, message)
        else:
            raise NotImplementedError()

    def _send_text_message(self, user_id: users.UserId, message: messages.TextMessage):
        data = {
            'recipient': {
                'id': user_id.id
            },
            'message': {
                'text': message.text
            },
            'messaging_type': TYPE_REPLY if triggers.SenderAspect in message.trigger else TYPE_SUBSCRIPTION,
        }

        return get_app().bot_interfaces['facebook']['api_interface'].post_send_api(data)

    def _send_template_message(self, user_id: users.UserId, message: 'TemplateMessage'):
        data = {
            'recipient': {
                'id': user_id.id
            },
            'message': {
                'attachment': {
                    'type': 'template',
                    'payload': message.payload
                }
            },
            'messaging_type': TYPE_REPLY if triggers.SenderAspect in message.trigger else TYPE_SUBSCRIPTION,
        }

        return get_app().bot_interfaces['facebook']['api_interface'].post_send_api(data)


class TemplateMessage(messages.Message):
    def __init__(self, trigger: messages.Trigger, payload):
        super().__init__(trigger)
        self.payload = payload
