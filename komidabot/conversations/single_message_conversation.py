from komidabot.conversations import ActionResult, Conversation, IConversationManager
from komidabot.messages import Trigger, Message
from komidabot.users import User


class SingleMessageConversation(Conversation):
    def __init__(self, user: User, manager: IConversationManager, message: Message):
        super().__init__(user, manager)
        self.message = message

    def conversation_started(self, _: Trigger):
        self.user.send_message(self.message)
        self.stop_conversation()

    def conversation_ended(self):
        pass  # Do nothing

    def trigger_received(self, _):
        return ActionResult.DEFER  # This conversation does not handle messages
