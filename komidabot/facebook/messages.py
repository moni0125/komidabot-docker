from flask import current_app as app

import komidabot.facebook.users
import komidabot.messages as messages
import komidabot.triggers as triggers
import komidabot.users as users

TYPE_REPLY = 'RESPONSE'
TYPE_SUBSCRIPTION = 'NON_PROMOTIONAL_SUBSCRIPTION'


class MessageHandler(messages.MessageHandler):
    def send_message(self, user: users.User, message: messages.Message):
        if user.id.provider != komidabot.facebook.users.UserManager.MANAGER_ID:
            raise ValueError('User id is not for Facebook')

        if isinstance(message, messages.TextMessage):
            self._send_text_message(user.id, message)
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
            'messaging_type': TYPE_REPLY if isinstance(message.trigger, triggers.UserTextTrigger) else TYPE_SUBSCRIPTION
        }

        return app.bot_interfaces['facebook']['api_interface'].post_send_api(data)

# TODO: Batch requests
