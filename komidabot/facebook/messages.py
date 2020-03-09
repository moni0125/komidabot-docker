import komidabot.facebook.constants as fb_constants
import komidabot.menu
import komidabot.messages as messages
import komidabot.triggers as triggers
import komidabot.users as users
from komidabot.app import get_app

TYPE_REPLY = 'RESPONSE'
TYPE_SUBSCRIPTION = 'NON_PROMOTIONAL_SUBSCRIPTION'


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message) -> messages.MessageSendResult:
        if user.id.provider != fb_constants.PROVIDER_ID:
            raise ValueError('User id is not for Facebook')

        if isinstance(message, messages.TextMessage):
            return self._send_text_message(user.id, message)
        elif isinstance(message, messages.MenuMessage):
            return self._send_menu_message(user, message)
        elif isinstance(message, TemplateMessage):
            return self._send_template_message(user.id, message)
        else:
            return messages.MessageSendResult.UNSUPPORTED

    @staticmethod
    def _send_text_message(user_id: users.UserId, message: messages.TextMessage) -> messages.MessageSendResult:
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

    @staticmethod
    def _send_menu_message(user: users.User, message: messages.MenuMessage) -> messages.MessageSendResult:
        text = komidabot.menu.get_menu_text(message.menu, message.translator, user.get_locale())

        if text is None:
            return messages.MessageSendResult.ERROR

        data = {
            'recipient': {
                'id': user.get_internal_id()
            },
            'message': {
                'text': text
            },
            'messaging_type': TYPE_REPLY if triggers.SenderAspect in message.trigger else TYPE_SUBSCRIPTION,
        }

        return get_app().bot_interfaces['facebook']['api_interface'].post_send_api(data)

    @staticmethod
    def _send_template_message(user_id: users.UserId, message: 'TemplateMessage') -> messages.MessageSendResult:
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
