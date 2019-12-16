import json

from typing import Callable

import komidabot.facebook.triggers as triggers

postback_mappings = {}


class Postback:
    def call_postback(self, trigger: triggers.Trigger, *args, **kwargs) -> triggers.Trigger:
        raise NotImplementedError()


def lookup_postback(name: str) -> Postback:
    return postback_mappings.get(name, None)


def postback(name: str = None):
    class PostbackDecorator(Postback):
        def __init__(self, func: Callable):
            nonlocal name

            if name is None:
                name = func.__name__

            if name in postback_mappings:
                raise ValueError('Duplicate postback identifier')

            postback_mappings[name] = self

            self.func = func
            self.__name__ = func.__name__

        def call_postback(self, trigger: triggers.Trigger, *args, **kwargs) -> triggers.Trigger:
            return self.func(trigger, *args, **kwargs)

        def __call__(self, *args, **kwargs):
            return json.dumps({'name': name, 'args': args, 'kwargs': kwargs})

    return PostbackDecorator


@postback(name='komidabot:get_started')
def get_started(trigger: triggers.Trigger):
    if triggers.NewUserAspect not in trigger:
        trigger.add_aspect(triggers.NewUserAspect())
    return trigger


@postback(name='komidabot:menu_today')
def menu_today(trigger: triggers.Trigger):
    return None


@postback(name='komidabot:settings_subscriptions')
def settings_subscriptions(trigger: triggers.Trigger):
    return None


@postback(name='komidabot:settings_language')
def settings_language(trigger: triggers.Trigger):
    return None


def generate_postback_data(include_persistent_menu: bool):
    result = dict()
    result['get_started'] = {
        'payload': get_started(),
    }
    result['greeting'] = [
        {
            'locale': 'default',
            'text': 'Welcome!',
        },
        {
            'locale': 'nl_BE',
            'text': 'Welkom!',
        },
        {
            'locale': 'nl_NL',
            'text': 'Welkom!',
        },
    ]
    if include_persistent_menu:
        # TODO: Once per-user persistent menus are available, use them
        #       https://developers.facebook.com/docs/messenger-platform/send-messages/persistent-menu/
        result['persistent_menu'] = [
            {
                'locale': 'default',
                'composer_input_disabled': False,
                'call_to_actions': [
                    {
                        'type': 'postback',
                        'title': "Today's Menu",
                        'payload': menu_today(),
                    },
                    {
                        'type': 'postback',
                        'title': 'Manage subscription',
                        'payload': settings_subscriptions(),
                    },
                    {
                        'type': 'postback',
                        'title': 'Change language',
                        'payload': settings_language(),
                    },
                ],
            },
        ]

    return result
