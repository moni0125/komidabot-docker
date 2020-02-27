import hashlib
import hmac
import json
import pprint
import sys
import time
import traceback
from functools import wraps
from typing import Dict

from flask import Blueprint, abort, request

import komidabot.facebook.constants as fb_constants
import komidabot.facebook.postbacks as postbacks
import komidabot.facebook.triggers as triggers
import komidabot.localisation as localisation
import komidabot.web.constants as web_constants
from extensions import db
from komidabot.app import get_app
from komidabot.debug.state import DebuggableException
from komidabot.facebook.users import User as FacebookUser
from komidabot.komidabot import Bot
from komidabot.messages import TextMessage
from komidabot.users import UnifiedUserManager, UserId, User
from komidabot.web.users import User as WebUser

blueprint = Blueprint('komidabot', __name__)
pp = pprint.PrettyPrinter(indent=2)


@blueprint.route('/', methods=['GET'])
def handle_facebook_verification():
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
def handle_facebook_webhook():
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
                    user = user_manager.get_user(UserId(sender, fb_constants.PROVIDER_ID),
                                                 event=event)  # type: FacebookUser

                    if not isinstance(user, FacebookUser):
                        # FIXME: Rather have a check that when the user supports "read" markers, we mark as read
                        raise RuntimeError('Expected Facebook User')

                    user.mark_message_seen()

                    app.task_executor.submit(_do_handle_facebook_webhook, event, user, app._get_current_object())

            return 'ok', 200

        print(pprint.pformat(data, indent=2), flush=True)

        return abort(400)
    except DebuggableException as e:
        app = get_app()
        app.bot.notify_error(e)

        e.print_info(app.logger)
    except Exception as e:
        try:
            get_app().bot.notify_error(e)
        except Exception:
            pass

        traceback.print_tb(e.__traceback__)
        print(e, flush=True, file=sys.stderr)

        return 'ok', 200


def _do_handle_facebook_webhook(event, user: User, app):
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
                #       What about messages that include attachments or other things?
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
                # print(pprint.pformat(event, indent=2), flush=True)

                if app.config.get('DISABLED'):
                    if not user.is_admin():
                        if triggers.AtAdminAspect not in trigger:
                            user.send_message(TextMessage(trigger, localisation.DOWN_FOR_MAINTENANCE(locale)))

                        return

                postback = event['postback']  # type: dict

                payload = postback.get('payload')

                try:
                    data = json.loads(payload)  # type: Dict
                except json.JSONDecodeError:
                    raise

                trigger = triggers.PostbackTrigger.extend(trigger, data['name'], data['args'], data['kwargs'])

                # TODO: This will be cleaner if we work with intents (see komidabot.py)
                postback_obj = postbacks.lookup_postback(trigger.name)

                if postback_obj:
                    trigger = postback_obj.call_postback(trigger, *trigger.args, **trigger.kwargs)

                    if trigger is None:
                        return  # Indicates the trigger was processed
                        # TODO: Again, this will be cleaner if we work with intents (see komidabot.py)
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
        except DebuggableException as e:
            app = get_app()
            app.bot.notify_error(e)

            e.print_info(app.logger)
        except Exception as e:
            try:
                app.logger.error('Error while handling event:\n{}'.format(pprint.pformat(event, indent=2)))
                get_app().bot.notify_error(e)
            except Exception:
                pass

            user.send_message(TextMessage(trigger, localisation.INTERNAL_ERROR(locale)))
            app.logger.exception(e)


@blueprint.route('/subscription', methods=['POST'])
def handle_facebook_verification():
    try:
        app = get_app()
        data = request.get_json()

        print(pprint.pformat(data, indent=2), flush=True)

        if data and 'subscription' in data:
            subscription = data['subscription']

            if 'endpoint' not in subscription:
                return abort(400)

            if 'keys' not in subscription:
                return abort(400)

            endpoint = subscription['endpoint']
            keys = subscription['keys']

            needs_commit = False

            user_manager = app.user_manager  # type: UnifiedUserManager
            user = user_manager.get_user(UserId(endpoint, web_constants.PROVIDER_ID))  # type: WebUser

            if user.get_db_user() is None:
                print('Adding new subscription to the database {}'.format(user.id), flush=True)
                user.add_to_db()
                user.set_data({
                    'keys': keys
                })
                needs_commit = True

            if needs_commit:
                db.session.commit()

            return 'ok', 200

        return abort(400)
    except DebuggableException as e:
        app = get_app()
        app.bot.notify_error(e)

        e.print_info(app.logger)

        return abort(500)
    except Exception as e:
        try:
            get_app().bot.notify_error(e)
        except Exception:
            pass

        traceback.print_tb(e.__traceback__)
        print(e, flush=True, file=sys.stderr)

        return abort(500)
