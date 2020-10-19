import datetime
import enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import komidabot.models as models
import komidabot.translation as translation


class Aspect:
    allows_multiple = False

    def __repr__(self):
        return 'Aspect'


T = TypeVar('T')


class Trigger:
    def __init__(self, aspects: List[Aspect] = None):
        self._aspects = dict()  # type: Dict[Type[Aspect], Union[List[Aspect], Aspect]]
        if aspects:
            for aspect in aspects:
                self.add_aspect(aspect)

    def add_aspect(self, aspect: Aspect, aspect_type: Type[Aspect] = None):
        aspect_type = aspect_type or type(aspect)
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
    def extend(cls: Type[T], trigger: 'Trigger', *args, aspects: List[Aspect] = None, **kwargs) -> T:
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

    def __repr__(self):
        result = self.get_repr_text()
        for aspect_type in self._aspects:
            result.append('- ' + repr(self._aspects[aspect_type]))

        return '\n'.join(result)

    def get_repr_text(self):
        return ['Trigger']


class Message:
    def __init__(self, trigger: Trigger):
        self.trigger = trigger


class TextMessage(Message):
    def __init__(self, trigger: Trigger, text: str):
        super().__init__(trigger)
        self.text = text


class MenuMessage(Message):
    def __init__(self, trigger: Trigger, menu: models.Menu, translator: translation.TranslationService):
        super().__init__(trigger)
        self.menu = menu
        self.translator = translator


class SubscriptionMenuMessage(Message):
    def __init__(self, trigger: Trigger, date: datetime.date, translator: translation.TranslationService):
        super().__init__(trigger)
        self.date = date
        self.translator = translator
        # campus id -> {language -> {user manager -> prepared message}}
        self.prepared_cache = dict()  # type: Dict[int, Dict[str, Dict[str, Any]]]

    def get_prepared(self, campus: models.Campus, lang: str, user_manager: str) -> Optional[Any]:
        if campus.id in self.prepared_cache:
            for_campus = self.prepared_cache[campus.id]
            if lang in for_campus:
                for_lang = for_campus[lang]
                if user_manager in for_lang:
                    return for_lang[user_manager]
        return None

    def set_prepared(self, campus: models.Campus, lang: str, user_manager: str, prepared: Any):
        if campus.id not in self.prepared_cache:
            self.prepared_cache[campus.id] = {}

        for_campus = self.prepared_cache[campus.id]
        if lang not in for_campus:
            for_campus[lang] = {}

        for_campus[lang][user_manager] = prepared


class MessageSendResult(enum.Enum):
    # Indicates successful message sending
    SUCCESS = 'Success'
    # Indicates an internal error when sending
    ERROR = 'Error'
    # Indicates an external error when sending
    EXTERNAL_ERROR = 'External error'
    # Indicates the message could not be sent because the user does not support receiving it
    UNSUPPORTED = 'Unsupported'
    # Indicates the user could not be reached, but could potentially be reached in the future
    UNREACHABLE = 'Unreachable'
    # Indicates the user no longer exists, the user should be removed from the database
    GONE = 'Gone'


class MessageHandler:
    # NOTE: There are some cases where the result of this method is important
    #       For example: When sending subscription messages, we cannot be certain the message will arrive, or the user
    #       may have unsubscribed and we need to remove their entry from the database.
    #       For cases where the message is a direct result of the user sending a message to us, we assume the message
    #       will be delivered without problems.
    def send_message(self, user, message: 'Message') -> 'MessageSendResult':
        raise NotImplementedError()
