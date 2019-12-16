from komidabot.triggers import *


class PostbackTrigger(Trigger):
    def __init__(self, name, d_args, d_kwargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.args = d_args
        self.kwargs = d_kwargs

    def get_repr_text(self):
        return ['PostbackTrigger',
                '- Name: ' + repr(self.name),
                '- args: ' + repr(self.args),
                '- kwargs: ' + repr(self.kwargs),
                ]
