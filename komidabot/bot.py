from komidabot.messages import Trigger


class Bot:
    def trigger_received(self, trigger: Trigger):
        raise NotImplementedError()

    # TODO: This should probably be a trigger instead
    def notify_error(self, error: Exception):
        raise NotImplementedError()
