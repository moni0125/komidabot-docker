import hashlib
import hmac
import pprint
import sys
import time
import traceback
from functools import wraps

from flask import Blueprint, abort, request

import komidabot.localisation as localisation
import komidabot.triggers as triggers
from komidabot.app import get_app
from komidabot.komidabot import Bot
from komidabot.messages import TextMessage
from komidabot.users import UnifiedUserManager, UserId, User
from komidabot.facebook.users import User as FacebookUser
from extensions import db

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
                    user = user_manager.get_user(UserId(sender, 'facebook'), event=event)  # type: FacebookUser

                    if not isinstance(user, FacebookUser):
                        # FIXME: Rather have a check that when the user supports "read" markers, we mark as read
                        raise RuntimeError('Expected Facebook User')

                    user.mark_message_seen()

                    app.task_executor.submit(_do_handle_message, event, user, app._get_current_object())

                return 'ok', 200

        print(pprint.pformat(data, indent=2), flush=True)

        return abort(400)
    except Exception as e:
        try:
            get_app().bot.notify_error(e)
        except Exception:
            pass

        traceback.print_tb(e.__traceback__)
        print(e, flush=True, file=sys.stderr)

        return 'ok', 200


def _do_handle_message(event, user: User, app):
    time.sleep(0.1)  # Yield

    with app.app_context():
        trigger = triggers.Trigger(aspects=[triggers.SenderAspect(user)])

        needs_commit = False

        if user.get_db_user() is None:
            trigger.add_aspect(triggers.NewUserAspect())
            print('Adding new user to the database {}'.format(user.id), flush=True)
            user.add_to_db()
            needs_commit = True

        bot: Bot = app.bot

        locale = user.get_locale()

        try:
            print('Handling message in new path for {}'.format(user.id), flush=True)
            # print(pprint.pformat(event, indent=2), flush=True)

            if 'message' in event:
                message = event['message']

                # print(pprint.pformat(message, indent=2), flush=True)

                # TODO: Is this the preferred way to differentiate inputs?
                # TODO: What about messages that include attachments or other things?
                # TODO: This now works with aspects rather than inheritance, so in theory this could be done
                if 'text' in message:
                    message_text = message['text']

                    trigger = triggers.TextTrigger.extend(trigger, message_text)

                    if '@admin' in message_text:
                        trigger.add_aspect(triggers.AtAdminAspect())

                    if 'nlp' in message:
                        if 'detected_locales' in message['nlp'] and len(message['nlp']['detected_locales']) > 0:
                            # Get the locale that has the highest confidence
                            locale_entry = max(message['nlp']['detected_locales'], key=lambda x: x['confidence'])
                            trigger.add_aspect(triggers.LocaleAspect(locale_entry['locale'],
                                                                     locale_entry['confidence']))
                            locale = locale_entry['locale']

                        if 'entities' in message['nlp']:
                            entities = message['nlp']['entities']

                            if 'datetime' in entities:
                                for entity in entities['datetime']:
                                    if 'value' in entity:  # Specific date given, vs. date range
                                        # FIXME: Do we want to add range datetimes?
                                        trigger.add_aspect(triggers.DatetimeAspect(entity['value'], entity['grain']))

                    if user.is_admin() and message_text == 'sub':
                        # Simulate subscription instead
                        trigger = triggers.SubscriptionTrigger.extend(trigger)

                if app.config.get('DISABLED'):
                    if not user.is_admin():
                        if triggers.AtAdminAspect not in trigger:
                            user.send_message(TextMessage(trigger, localisation.DOWN_FOR_MAINTENANCE(locale)))

                        return

                    # sender_obj.send_text_message('Note: The bot is currently disabled')

            elif 'postback' in event:
                print(pprint.pformat(event, indent=2), flush=True)

                postback = event['postback']  # type: dict

                payload = postback.get('payload')

                if payload == 'komidabot:get_started':
                    trigger.add_aspect(triggers.NewUserAspect())
                else:
                    get_app().bot.message_admins(TextMessage(triggers.Trigger(), 'Unknown postback type received!'))
                    user.send_message(TextMessage(trigger, localisation.ERROR_POSTBACK(locale)))
                    return
            else:
                print(pprint.pformat(event, indent=2), flush=True)

                get_app().bot.message_admins(TextMessage(triggers.Trigger(), 'Unknown message type received!'))

                return

            bot.trigger_received(trigger)

            if needs_commit:
                db.session.commit()
        except Exception as e:
            try:
                app.logger.error('Error while handling event:\n{}'.format(pprint.pformat(event, indent=2)))
                get_app().bot.notify_error(e)
            except Exception:
                pass

            user.send_message(TextMessage(trigger, localisation.INTERNAL_ERROR(locale)))
            app.logger.exception(e)

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
