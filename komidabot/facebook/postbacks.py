import json
from typing import Callable, Optional

import komidabot.facebook.triggers as triggers
import komidabot.facebook.messages as fb_messages
import komidabot.messages as messages
from extensions import db

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

        def call_postback(self, trigger: triggers.Trigger, *args, **kwargs) -> Optional[triggers.Trigger]:
            return self.func(trigger, *args, **kwargs)

        def __call__(self, *args, **kwargs):
            return json.dumps({'name': name, 'args': args, 'kwargs': kwargs})

    return PostbackDecorator


def postback_button(title: str, payload: str):
    return {'type': 'postback', 'title': title, 'payload': payload}


@postback(name='komidabot:get_started')
def get_started(trigger: triggers.Trigger):
    if triggers.NewUserAspect not in trigger:
        trigger.add_aspect(triggers.NewUserAspect())
    return trigger


@postback(name='komidabot:menu_today')
def menu_today(trigger: triggers.Trigger):
    return trigger


@postback(name='komidabot:settings_subscriptions')
def settings_subscriptions(trigger: triggers.Trigger):
    if triggers.SenderAspect not in trigger:
        raise ValueError('Trigger missing SenderAspect')
    sender = trigger[triggers.SenderAspect].sender

    payload = {
        'template_type': 'generic',
        'elements': [
            {
                'title': 'Monday',
                'image_url': 'https://komidabot.heldplayer.blue/images/monday.png',
                'buttons': [
                    postback_button("Unsubscribe", set_subscription(1, None)),
                    postback_button("Campus Middelheim", set_subscription(1, 'cmi')),
                    postback_button("Campus Drie Eiken", set_subscription(1, 'cde')),
                ]
            },
            {
                'title': 'Monday (cont.)',
                'image_url': 'https://komidabot.heldplayer.blue/images/monday.png',
                'buttons': [
                    postback_button("Stadscampus", set_subscription(1, 'cst')),
                    postback_button("Campus Groenenborger", set_subscription(1, 'cgb')),
                    postback_button("Hogere Zeevaartschool", set_subscription(1, 'hzs')),
                ]
            },
        ],
    }
    sender.send_message(fb_messages.TemplateMessage(trigger, payload))

    return None


@postback(name='komidabot:set_language')
def set_subscription(trigger: triggers.Trigger, day: int, campus: str):
    if triggers.SenderAspect not in trigger:
        raise ValueError('Trigger missing SenderAspect')
    sender = trigger[triggers.SenderAspect].sender

    sender.send_message(messages.TextMessage(trigger, 'This feature is currently not supported'))

    return None


@postback(name='komidabot:settings_language')
def settings_language(trigger: triggers.Trigger):
    if triggers.SenderAspect not in trigger:
        raise ValueError('Trigger missing SenderAspect')
    sender = trigger[triggers.SenderAspect].sender

    payload = {
        'template_type': 'button',
        'text': 'Chose your desired language',
        'buttons': [
            postback_button("Nederlands", set_language('nl_BE', 'Nederlands')),
            postback_button("English", set_language('en_US', 'English')),
            postback_button("From Facebook", set_language('', 'From Facebook')),
        ],
    }
    sender.send_message(fb_messages.TemplateMessage(trigger, payload))

    return None


@postback(name='komidabot:set_language')
def set_language(trigger: triggers.Trigger, language: str, display: str):
    if triggers.SenderAspect not in trigger:
        raise ValueError('Trigger missing SenderAspect')
    sender = trigger[triggers.SenderAspect].sender

    sender.get_db_user().set_language(language)
    db.session.commit()

    sender.send_message(messages.TextMessage(trigger, 'Your language is now set to: {}'.format(display)))

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
                    postback_button("Today's menu", menu_today()),
                    postback_button("Manage subscription", settings_subscriptions()),
                    postback_button("Change language", settings_language()),
                ],
            },
        ]

    return result
