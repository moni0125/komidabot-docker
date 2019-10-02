from typing import Hashable


class MessageReceiver:
    def send_message(self, message):
        raise NotImplementedError

    def send_text_message(self, message: str):
        raise NotImplementedError

    def get_id(self) -> Hashable:
        raise NotImplementedError
