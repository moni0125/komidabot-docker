from functools import wraps
import hashlib, hmac, pprint, sys, time, traceback

from flask import Blueprint, abort, request

from komidabot.app import get_app

from komidabot.facebook.received_message import MessageSender as LegacyMessageSender, \
    NLPAttribute as LegacyNLPAttribute, ReceivedTextMessage as LegacyReceivedTextMessage
from komidabot.komidabot import Komidabot, Bot
from komidabot.messages import TextMessage
from komidabot.triggers import AnnotatedUserTextTrigger, NLPAttribute, SubscriptionTrigger, UserTrigger
from komidabot.users import UnifiedUserManager, UserId, User

import komidabot.localisation as localisation

blueprint = Blueprint('komidabot', __name__)
pp = pprint.PrettyPrinter(indent=2)


@blueprint.route('/', methods=['GET'])
def handle_verification():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get('hub.verify_token', '') == get_app().config['VERIFY_TOKEN']:
            print("Verified")
            return request.args.get('hub.challenge', '')
        else:
            print("Wrong token")
            return "Error, wrong validation token"
    else:
        return abort(401)


def validate_signature(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        if get_app().config['TESTING']:
            # Skip validating signature if we're testing
            return func(*args, **kwargs)

        advertised = request.headers.get("X-Hub-Signature")
        if advertised is None:
            return False

        advertised = advertised.replace("sha1=", "", 1)
        data = request.get_data()

        received = hmac.new(
            key=get_app().config['APP_SECRET'].encode('raw_unicode_escape'),
            msg=data,
            digestmod=hashlib.sha1
        ).hexdigest()

        if hmac.compare_digest(advertised, received):
            return func(*args, **kwargs)

        return abort(401)

    return decorated_func


@blueprint.route('/', methods=['POST'])
@validate_signature
def handle_message():
    try:
        app = get_app()
        data = request.get_json()

        if data and data['object'] == 'page':
            for entry in data['entry']:  # type: dict
                if 'messaging' not in entry:
                    continue

                for event in entry['messaging']:
                    sender = event["sender"]["id"]
                    # recipient = event["recipient"]["id"]

                    user_manager = app.user_manager  # type: UnifiedUserManager
                    user = user_manager.get_user(UserId(sender, 'facebook'), event=event)

                    sender_obj = LegacyMessageSender(sender)
                    sender_obj.mark_seen()

                    if user.is_feature_active('new_messaging'):
                        app.task_executor.submit(_do_handle_message, event, user, app._get_current_object())
                    else:
                        app.task_executor.submit(_do_handle_message_legacy, event, sender_obj,
                                                 app._get_current_object())

                return 'ok', 200

        print(pprint.pformat(data, indent=2), flush=True)

        return abort(400)
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e, flush=True, file=sys.stderr)

        return 'ok', 200


def _do_handle_message(event, user: User, app):
    time.sleep(0.1)  # Yield

    with app.app_context():
        trigger = UserTrigger(user)

        bot: Bot = app.bot

        try:
            print('Handling message in new path for {}'.format(user.id), flush=True)
            print(pprint.pformat(event, indent=2), flush=True)

            if 'message' in event:
                message = event['message']

                # print(pprint.pformat(message, indent=2), flush=True)

                # TODO: Is this the preferred way to differentiate inputs?
                # TODO: What about messages that include attachments or other things?
                if 'text' in message:
                    trigger = AnnotatedUserTextTrigger(message['text'], trigger.sender)

                    message_text = message['text']

                    if 'admin' in message_text:
                        return  # TODO: Handle properly in the future

                    if 'nlp' in message:
                        if 'detected_locales' in message['nlp']:
                            for locale_entry in message['nlp']['detected_locales']:
                                trigger.add_attribute(NLPAttribute('locale', locale_entry['locale'],
                                                                   locale_entry['confidence']))
                        if 'entities' in message['nlp']:
                            for attribute, nlp_entries in message['nlp']['entities'].items():
                                for nlp_entry in nlp_entries:
                                    attribute_obj = NLPAttribute(attribute, nlp_entry['confidence'], nlp_entry)
                                    trigger.add_attribute(attribute_obj)

                    if user.is_admin() and message_text == 'sub':
                        # Simulate subscription instead
                        trigger = SubscriptionTrigger()

                if app.config.get('DISABLED'):
                    if not user.is_admin():
                        user.send_message(TextMessage(trigger, localisation.DOWN_FOR_MAINTENANCE1(user.get_locale())))
                        user.send_message(TextMessage(trigger, localisation.DOWN_FOR_MAINTENANCE2(user.get_locale())))
                        return

                    # sender_obj.send_text_message('Note: The bot is currently disabled')

                bot.trigger_received(trigger)
            elif 'postback' in event:
                user.send_message(TextMessage(trigger, localisation.ERROR_POSTBACK(user.get_locale())))
                # postback = event['postback']

                # sender_obj.send_text_message(localisation.ERROR_NOT_IMPLEMENTED(sender_obj.get_locale()))
        except Exception as e:
            user.send_message(TextMessage(trigger, localisation.INTERNAL_ERROR(user.get_locale())))
            app.logger.exception(e)
            # traceback.print_tb(e.__traceback__)
            # print(e, flush=True, file=sys.stderr)


# komidabot_1     | { 'message': { 'attachments': [ { 'payload': { 'sticker_id': 369239263222822,
# komidabot_1     |                                                'url': 'https://scontent.xx.fbcdn.net/v/t39.1997-6/39
# 178562_1505197616293642_5411344281094848512_n.png?_nc_cat=1&_nc_oc=AQm57VHu6KQauDTkvWGzNJE91vLieGwdA9u0sTl2KhZy8gUqm3z
# VoJvQ5knybEoLjpw5VVichzB1EhmnJn1E4Zk9&_nc_ad=z-m&_nc_cid=0&_nc_zor=9&_nc_ht=scontent.xx&oh=61f57a8ed4a3af09213c822d72f
# 31b1b&oe=5DF3C875'},
# komidabot_1     |                                   'type': 'image'}],
# komidabot_1     |                'mid': 'OirMBeRGhQyTecBQ8BlIBbe3mqAMHtRIwdiwiPtxsjmrNKAH5-s8dwxob_2KszvHRbSdApenwZfud
# 6VGt9IKwA',
# komidabot_1     |                'sticker_id': 369239263222822},
# komidabot_1     |   'recipient': {'id': '1502601723123151'},
# komidabot_1     |   'sender': {'id': '1468689523250850'},
# komidabot_1     |   'timestamp': 1570008603230}


def _do_handle_message_legacy(event, sender_obj: LegacyMessageSender, app):
    time.sleep(0.1)  # Yield

    with app.app_context():
        print('Handling message in legacy path', flush=True)
        print(pprint.pformat(event, indent=2), flush=True)

        komidabot: Komidabot = app.komidabot

        if 'message' in event:
            message = event['message']

            # print(pprint.pformat(message, indent=2), flush=True)

            if 'text' not in message:
                sender_obj.send_text_message(localisation.ERROR_TEXT_ONLY(sender_obj.get_locale()))
                return

            message_text = message['text']

            if 'admin' in message_text:
                return

            message_obj = LegacyReceivedTextMessage(sender_obj, message_text)

            if 'nlp' in message:
                if 'detected_locales' in message['nlp']:
                    for locale_entry in message['nlp']['detected_locales']:
                        message_obj.add_attribute(LegacyNLPAttribute('locale', locale_entry['locale'],
                                                                     locale_entry['confidence']))
                if 'entities' in message['nlp']:
                    for attribute, nlp_entries in message['nlp']['entities'].items():
                        for nlp_entry in nlp_entries:
                            attribute_obj = LegacyNLPAttribute(attribute, nlp_entry['confidence'], nlp_entry)
                            message_obj.add_attribute(attribute_obj)

            if app.config.get('DISABLED'):
                if not sender_obj.is_admin():
                    sender_obj.send_text_message(localisation.DOWN_FOR_MAINTENANCE1(sender_obj.get_locale()))
                    sender_obj.send_text_message(localisation.DOWN_FOR_MAINTENANCE2(sender_obj.get_locale()))
                    return

                # sender_obj.send_text_message('Note: The bot is currently disabled')

            print(repr(message_obj), flush=True)

            try:
                komidabot.message_received_legacy(message_obj)
            except Exception as e:
                sender_obj.send_text_message(localisation.INTERNAL_ERROR(sender_obj.get_locale()))
                app.logger.exception(e)
                # traceback.print_tb(e.__traceback__)
                # print(e, flush=True, file=sys.stderr)
        elif 'postback' in event:
            sender_obj.send_text_message(localisation.ERROR_POSTBACK(sender_obj.get_locale()))
            # postback = event['postback']

            # sender_obj.send_text_message(localisation.ERROR_NOT_IMPLEMENTED(sender_obj.get_locale()))
