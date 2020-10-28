import atexit
import datetime
import threading
from typing import List

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import komidabot.external_menu as external_menu
import komidabot.facebook.nlp_dates as nlp_dates
import komidabot.localisation as localisation
import komidabot.messages as messages
import komidabot.triggers as triggers
from extensions import db
from komidabot.app import get_app
from komidabot.bot import Bot
from komidabot.debug.state import DebuggableException, ProgramStateTrace, SimpleProgramState
from komidabot.models import Campus, ClosingDays, Day, Menu
from komidabot.models import create_standard_values, import_dump, recreate_db


class Komidabot(Bot):
    def __init__(self, the_app):
        self.lock = threading.Lock()

        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': ThreadPoolExecutor(max_workers=4)},
            job_defaults={'misfire_grace_time': 60}
        )

        self._handling_error = False

        self.scheduler.start()
        atexit.register(BackgroundScheduler.shutdown, self.scheduler)  # Ensure cleanup of resources

        # Scheduled jobs should work with DST

        @self.scheduler.scheduled_job(CronTrigger(day_of_week='mon-fri', hour=10, minute=0, second=0),
                                      args=(the_app.app_context, self),
                                      id='daily_menu', name='Daily menu notifications')
        def daily_menu(context, bot: 'Komidabot'):
            with context():
                if get_app().config.get('DISABLED'):
                    return

                bot.trigger_received(triggers.SubscriptionTrigger())

        @self.scheduler.scheduled_job(CronTrigger(minute=0, second=0),  # Run every hour to find changes
                                      args=(the_app.app_context, self),
                                      id='menu_update', name='Hourly update of the menus')
        def menu_update(context, bot: 'Komidabot'):
            with context():
                if get_app().config.get('DISABLED'):
                    return

                try:
                    today = datetime.datetime.today().date()
                    week_start = today + datetime.timedelta(days=-today.weekday())

                    dates = [week_start + datetime.timedelta(days=i) for i in range(today.weekday(), 5)]
                    if today.weekday() >= 3:
                        dates += [week_start + datetime.timedelta(days=7 + i) for i in range(5)]

                    update_menus(dates=dates)
                except DebuggableException as e:
                    bot.notify_error(e)

                    e.print_info(get_app().logger)
                except Exception as e:
                    bot.notify_error(e)

                    get_app().logger.exception(e)

    def trigger_received(self, trigger: triggers.Trigger):
        with self.lock:  # TODO: Maybe only lock on critical sections?
            app = get_app()
            verbose = app.config.get('VERBOSE')

            if verbose:
                print('Komidabot received a trigger: {}'.format(type(trigger).__name__), flush=True)
                print(repr(trigger), flush=True)

            if isinstance(trigger, triggers.SubscriptionTrigger):
                dispatch_daily_menus(trigger)
                return

            if triggers.AtAdminAspect in trigger:
                return  # Don't process messages targeted at the admin

            locale = None
            message_handled = False

            # XXX: Disabled once more because responses aren't reliably in the language the user expects it to be
            # if triggers.LocaleAspect in trigger and trigger[triggers.LocaleAspect].confidence > 0.9:
            #     locale = trigger[triggers.LocaleAspect].locale

            if triggers.SenderAspect in trigger:
                sender = trigger[triggers.SenderAspect].sender
                campuses = Campus.get_all()

                # This ensures that when a user is marked as reachable in case they were unreachable at some point
                # TODO: We no longer mark users as reachable, need to think over the proper course of action
                # if sender.mark_reachable():
                #     db.session.commit()

                if locale is None:
                    locale = sender.get_locale()

                if triggers.NewUserAspect in trigger:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NEW_USER(locale)))
                    msg = localisation.REPLY_INSTRUCTIONS(locale).format(
                        campuses=', '.join([campus.short_name.lower() for campus in campuses if campus.active])
                    )
                    sender.send_message(messages.TextMessage(trigger, msg))
                    sender.set_is_notified_new_site(True)
                    db.session.commit()

                    message_handled = True

                # TODO: Is this really how we want to handle input?
                #       Maybe we can add an IntentAspect, where the intent is the desired action the bot should take
                #       next? Ex. intents: admin message, get help, get menu, set preference (language, subscriptions)
                if isinstance(trigger, triggers.TextTrigger):
                    text = trigger.text
                    split = text.lower().split(' ')

                    if sender.is_admin():
                        if split[0] == 'setup':
                            if app.config.get('PRODUCTION'):
                                sender.send_message(messages.TextMessage(trigger, 'Not running setup on production'))
                                return
                            recreate_db()
                            create_standard_values()
                            import_dump(app.config['DUMP_FILE'])
                            sender.send_message(messages.TextMessage(trigger, 'Setup done'))
                            return
                        elif split[0] == 'update':
                            sender.send_message(messages.TextMessage(trigger, 'Updating menus...'))
                            update_menus(*split[1:])
                            sender.send_message(messages.TextMessage(trigger, 'Done updating menus...'))
                            return
                        elif split[0] == 'psid':  # TODO: Deprecated?
                            sender.send_message(messages.TextMessage(trigger, 'Your ID is {}'.format(sender.id.id)))
                            return

                    # TODO: Allow users to send more manual commands
                    #       See also the note prefacing the containing block
                    if not message_handled and split[0] == 'help':
                        msg = localisation.REPLY_INSTRUCTIONS(locale).format(
                            campuses=', '.join([campus.short_name.lower() for campus in campuses if campus.active])
                        )
                        sender.send_message(messages.TextMessage(trigger, msg))
                        return

                if app.config.get('COVID19_DISABLED'):
                    sender.send_message(messages.TextMessage(trigger, localisation.COVID19_UNAVAILABLE(locale)))
                    return

                requested_dates = []
                default_date = False

                if triggers.DatetimeAspect in trigger:
                    date_times = trigger[triggers.DatetimeAspect]
                    # TODO: Date parsing needs improving
                    requested_dates, invalid_date = nlp_dates.extract_days(date_times)

                    if invalid_date:
                        sender.send_message(messages.TextMessage(trigger, localisation.REPLY_INVALID_DATE(locale)))
                        return

                if len(requested_dates) > 1:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_TOO_MANY_DAYS(locale)))
                    return
                elif len(requested_dates) == 1:
                    date = requested_dates[0]
                else:
                    default_date = True
                    date = datetime.datetime.now().date()

                # TODO: How about getting the menu for the next day after a certain time of day?
                #       Only if we're returning the default day

                day = Day(date.isoweekday())

                if day == Day.SATURDAY or day == Day.SUNDAY:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_WEEKEND(locale)))
                    return

                requested_campuses = []
                default_campus = False

                if isinstance(trigger, triggers.TextTrigger):
                    text = trigger.text.lower()
                    for campus in campuses:
                        if not campus.active:
                            continue

                        for kw in campus.get_keywords():
                            if text.count(kw) > 0:
                                requested_campuses.append(campus)
                                break  # Prevent the same campus from being added multiple times

                if len(requested_campuses) > 1:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_TOO_MANY_CAMPUSES(locale)))
                    return
                elif len(requested_campuses) == 1:
                    campus = requested_campuses[0]
                else:
                    default_campus = True
                    campus = sender.get_campus_for_day(date)

                    if campus is None:  # User has no campus for the specified day
                        campus = Campus.get_by_short_name('cmi')

                if not campus.active:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_CAMPUS_INACTIVE(locale)
                                                             .format(campus=campus.name)))
                    return

                if message_handled and default_campus and default_date:
                    if isinstance(trigger, triggers.TextTrigger):
                        for word in ['menu', 'lunch', 'eten']:
                            if word in trigger.text:
                                break
                        else:
                            return
                    else:
                        return

                # if default_date and default_campus:
                #     if isinstance(trigger, triggers.TextTrigger):
                #         sender.send_message(messages.TextMessage(trigger,
                # localisation.REPLY_NO_DATE_OR_CAMPUS(locale)))
                #         msg = localisation.REPLY_INSTRUCTIONS(locale).format(
                #             campuses=', '.join([campus.short_name for campus in campuses])
                #         )
                #         sender.send_message(messages.TextMessage(trigger, msg))
                #         return
                #
                #     # User did not send a text message, so we'll continue anyway

                if not default_campus:
                    sender.set_campus_for_day(campus, date)
                    db.session.commit()

                if sender.get_is_notified_new_site() is False and sender.is_feature_active('new_site_notifications'):
                    if sender.send_message(messages.TextMessage(trigger, localisation.MESSAGE_NEW_SITE(locale))) \
                            == messages.MessageSendResult.SUCCESS:
                        sender.set_is_notified_new_site(True)
                        db.session.commit()

                closed = ClosingDays.find_is_closed(campus, date)

                if closed:
                    translation = closed.translatable.get_translation(locale, app.translator)

                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_CAMPUS_CLOSED(locale)
                                                             .format(campus=campus.name, date=str(date),
                                                                     reason=translation.translation)))
                    return

                # menu = komidabot.menu.prepare_menu_text(campus, date, app.translator, locale)
                menu = Menu.get_menu(campus, date)

                if menu is None:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NO_MENU(locale)
                                                             .format(campus=campus.name, date=str(date))))
                else:
                    # sender.send_message(messages.TextMessage(trigger, menu))
                    sender.send_message(messages.MenuMessage(trigger, menu, app.translator))

                # XXX: Disabled experiment
                # if default_date and default_campus and isinstance(trigger, triggers.TextTrigger):
                #     for keyword in ['lunch', 'menu', 'komida']:
                #         if keyword.lower() in trigger.text.lower():
                #             break
                #     else:
                #         sender.send_message(messages.TextMessage(trigger, localisation.REPLY_USE_AT_ADMIN(locale)))

    def notify_error(self, error: Exception):
        if self._handling_error:
            # Already handling an error, or we failed handling the previous error, so don't try handling more
            return
        self._handling_error = True

        self.message_admins(messages.ExceptionMessage(triggers.Trigger(), error))

        self._handling_error = False

    def message_admins(self, message: messages.Message):
        from komidabot.debug.administration import notify_admins

        with self.lock:
            notify_admins(message)

    def handle_ipc(self, data):
        print('Received IPC message:', data, flush=True)
        if not isinstance(data, dict):
            raise ValueError('Expected dictionary')
        if 'action' not in data:
            raise ValueError('Missing action')

        action = data['action']

        if action == 'sub':
            self.trigger_received(triggers.SubscriptionTrigger())
        elif action == 'update_menu':
            update_menus()
        elif action == 'cleanup':
            Menu.remove_menus_on_closing_days()

            db.session.commit()
        elif action == 'synchronize_menus':
            today = datetime.date.today() - datetime.timedelta(days=-7)

            start = datetime.date(2019, 11, 18)
            start = start + datetime.timedelta(days=-start.weekday())

            dates: List[datetime.datetime] = []
            while start < today:
                dates += [start + datetime.timedelta(days=i) for i in range(5)]
                start = start + datetime.timedelta(days=7)

            update_menus(dates=dates)


def dispatch_daily_menus(trigger: triggers.SubscriptionTrigger):
    from komidabot.subscriptions.daily_menu import CHANNEL_ID as DAILY_MENU_ID

    # limiter = Limiter(20)  # Limit to 20 messages per second

    date = trigger.date or datetime.datetime.now().date()
    day = Day(date.isoweekday())

    app = get_app()

    verbose = app.config.get('VERBOSE')

    if verbose:
        print('Sending out subscription for {} ({})'.format(date, day.name), flush=True)

    message = messages.SubscriptionMenuMessage(trigger, date, app.translator)
    app.subscription_manager.deliver_message(DAILY_MENU_ID, message)

    # user_manager = app.user_manager
    # changed = False
    #
    # subscribed_users = user_manager.get_subscribed_users(day)
    # subscriptions: Dict[Campus, List[users.User]] = dict()
    #
    # for user in subscribed_users:
    #     if app.config.get('DISABLED') and not user.is_admin():
    #         continue
    #
    #     if not user.is_feature_active('menu_subscription'):
    #         if verbose:
    #             print('User {} not eligible for subscription'.format(user.id), flush=True)
    #         continue
    #
    #     subscription = user.get_subscription_for_day(date)
    #     if subscription is None:
    #         continue
    #     if not subscription.active:
    #         continue
    #
    #     campus = subscription.campus
    #
    #     if not campus.active:
    #         continue
    #
    #     if campus not in subscriptions:
    #         subscriptions[campus] = []
    #
    #     subscriptions[campus].append(user)
    #
    # for campus, sub_users in subscriptions.items():
    #     if verbose:
    #         print('Preparing menu for {}'.format(campus.short_name), flush=True)
    #
    #     closed = ClosingDays.find_is_closed(campus, date)
    #
    #     if closed:
    #         continue  # Campus closed, no daily menu
    #
    #     # TODO: Change menus from TextMessage to a custom message type to support different formatting per platform
    #     menu = Menu.get_menu(campus, date)
    #     if menu is None:
    #         continue
    #
    #     for user in sub_users:
    #         limiter()  # Ensure we don't send too many messages at once
    #
    #         if verbose:
    #             print('Sending menu for {} to {}'.format(campus.short_name, user.id), flush=True)
    #         message_result = user.send_message(messages.MenuMessage(trigger, menu, app.translator))
    #
    #         if message_result == messages.MessageSendResult.UNSUPPORTED:
    #             # Text messages unsupported? Disable subscription then
    #             print('User {} does not support messages, removing from subscription list'.format(user.id),
    #                   flush=True)
    #
    #             user.mark_unreachable()
    #             changed = True
    #         if message_result == messages.MessageSendResult.UNREACHABLE:
    #             # Unreachable = Facebook is blocking us from sending, stop trying to send in the future
    #             print('User {} is unreachable, removing from subscription list'.format(user.id), flush=True)
    #
    #             user.mark_unreachable()
    #             changed = True
    #         if message_result == messages.MessageSendResult.GONE:
    #             # Gone = User no longer exists, delete from database
    #             print('User {} is gone, removing from database'.format(user.id), flush=True)
    #
    #             user.delete()
    #             changed = True
    #
    # if changed:
    #     db.session.commit()


def update_menus(*campuses: str, dates: 'List[datetime.date]' = None):
    debug_state = ProgramStateTrace()

    campus_list = Campus.get_all_active()

    if len(campuses) > 0:
        campus_list = [campus for campus in campus_list if campus.short_name not in campuses]

    if not dates:
        today = datetime.datetime.today().date()
        dates = [
            today,
            today + datetime.timedelta(days=1),
            today + datetime.timedelta(days=2),
            today + datetime.timedelta(days=3),
            today + datetime.timedelta(days=4),
            today + datetime.timedelta(days=5),
            today + datetime.timedelta(days=6),
            today + datetime.timedelta(days=7),
        ]

    for campus in campus_list:
        for date in dates:
            if date.isoweekday() in [6, 7]:
                continue

            closed = ClosingDays.find_is_closed(campus, date)

            if closed:
                continue  # Campus closed, don't try to find a menu

            with debug_state.state(SimpleProgramState('Campus menu update', {'campus': campus.short_name,
                                                                             'date': str(date)})):
                data_raw = external_menu.fetch_raw(campus, date)
                data_parsed = external_menu.parse_fetched(data_raw)
                data_processed = external_menu.process_parsed(data_parsed)

                assert campus.short_name == data_processed['campus']
                assert date.isoformat() == data_processed['date']

                external_menu.update_menu(data_processed)

    db.session.commit()
