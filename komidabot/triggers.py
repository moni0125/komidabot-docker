import komidabot.users as users
import komidabot.messages as messages


class SubscriptionTrigger(messages.Trigger):
    pass


class TextTrigger(messages.Trigger):
    def __init__(self, text):
        self.text = text


class MessageTrigger(messages.Trigger):
    def __init__(self, sender: users.User):
        self.sender = sender


class TextMessageTrigger(TextTrigger, MessageTrigger):
    def __init__(self, text, sender):
        TextTrigger.__init__(self, text)
        MessageTrigger.__init__(self, sender)


class AdminActionTrigger(messages.Trigger):
    def __init__(self, sub_trigger: messages.Trigger):
        self.sub_trigger = sub_trigger
