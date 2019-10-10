import datetime

from komidabot.conversations import ActionResult, Conversation
from komidabot.messages import Trigger, TextMessage
from komidabot.models import Campus
from komidabot.users import User


class SubscriptionConversation(Conversation):
    def __init__(self, user: User, campus: Campus, date: datetime.date, prepared_message: str):
        super().__init__(user)
        self.campus = campus
        self.date = date
        self.prepared_message = prepared_message

    def conversation_started(self, trigger: Trigger):
        self.user.send_message(TextMessage(trigger, self.prepared_message))

    def conversation_ended(self):
        pass  # Do nothing

    def trigger_received(self, _):
        return ActionResult.DEFER  # This conversation does not handle messages
