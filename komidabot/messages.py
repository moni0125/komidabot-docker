from typing import Dict, List, Type, TypeVar, Union


class Aspect:
    allows_multiple = False


T = TypeVar('T')


class Trigger:
    def __init__(self, aspects: List[Aspect] = None):
        self._aspects = dict()  # type: Dict[Type[Aspect], Union[List[Aspect], Aspect]]
        if aspects:
            for aspect in aspects:
                self.add_aspect(aspect)

    def add_aspect(self, aspect: Aspect):
        aspect_type = type(aspect)
        if aspect_type in self._aspects:
            if aspect_type.allows_multiple:
                self._aspects[aspect_type].append(aspect)
            else:
                raise ValueError('Cannot add multiple aspects for ' + aspect_type.__name__)
        else:
            if aspect_type.allows_multiple:
                self._aspects[aspect_type] = [aspect]
            else:
                self._aspects[aspect_type] = aspect

    def __contains__(self, aspect_type: Type[Aspect]) -> bool:
        return aspect_type in self._aspects

    def __getitem__(self, aspect_type: Type[T]) -> Union[List[T], T]:
        return self._aspects[aspect_type]

    def __delitem__(self, aspect_type: Type[Aspect]):
        del self._aspects[aspect_type]

    @classmethod
    def extend(cls, trigger: 'Trigger', *args, aspects: List[Aspect] = None, **kwargs):
        new_instance = cls(*args, **kwargs)
        for aspect_type in trigger._aspects:
            if not aspect_type.allows_multiple:
                new_instance.add_aspect(trigger._aspects[aspect_type])
            else:
                for aspect in trigger._aspects[aspect_type]:
                    new_instance.add_aspect(aspect)

        if aspects:
            for aspect in aspects:
                new_instance.add_aspect(aspect)

        return new_instance


class Message:
    def __init__(self, trigger: Trigger):
        self.trigger = trigger


class TextMessage(Message):
    def __init__(self, trigger: Trigger, text: str):
        super().__init__(trigger)
        self.text = text


class MessageHandler:
    def send_message(self, user, message: 'Message'):
        raise NotImplementedError()
