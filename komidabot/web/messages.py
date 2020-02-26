import komidabot.messages as messages
import komidabot.users as users
import komidabot.web.constants as web_constants


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message) -> messages.MessageSendResult:
        if user.id.provider != web_constants.PROVIDER_ID:
            raise ValueError('User id is not for Web')

        if isinstance(message, messages.TextMessage):
            return self._send_text_message(user, message)
        else:
            return messages.MessageSendResult.UNSUPPORTED

    @staticmethod
    def _send_text_message(user_id: users.User, message: messages.TextMessage) -> messages.MessageSendResult:
        return messages.MessageSendResult.UNSUPPORTED
