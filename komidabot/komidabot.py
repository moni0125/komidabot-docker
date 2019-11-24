import atexit
import datetime
import threading
from decimal import Decimal
from typing import Dict, List, Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import komidabot.external_menu as external_menu
import komidabot.facebook.nlp_dates as nlp_dates
import komidabot.localisation as localisation
import komidabot.menu
import komidabot.menu_scraper as menu_scraper
import komidabot.messages as messages
import komidabot.triggers as triggers
import komidabot.users as users
from extensions import db
from komidabot.app import get_app
from komidabot.bot import Bot
from komidabot.models import Campus, ClosingDays, Day, FoodType, Menu, Translatable
from komidabot.models import create_standard_values, import_dump, recreate_db


class Komidabot(Bot):
    def __init__(self, the_app):
        self.lock = threading.Lock()

        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': ThreadPoolExecutor(max_workers=1)}
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

        # FIXME: This is disabled for now
        # @self.scheduler.scheduled_job(CronTrigger(hour=1, minute=0, second=0),  # Run every day to find changes
        #                               args=(the_app.app_context, self),
        #                               id='menu_update', name='Daily late-night update of the menus')
        # def menu_update(context, bot: 'Komidabot'):
        #     with context():
        #         if get_app().config.get('DISABLED'):
        #             return
        #
        #         bot.update_menus(None)

        # FIXME: This is disabled until some changes are done to updating menus
        # @self.scheduler.scheduled_job(CronTrigger(hour=1, minute=0, second=0),  # Run every day to find changes
        #                               args=(the_app.app_context, self),
        #                               id='menu_update', name='Daily late-night update of the menus')
        # def menu_update(context, bot: 'Komidabot'):
        #     with context():
        #         if get_app().config.get('DISABLED'):
        #             return
        #
        #         try:
        #             today = datetime.datetime.today().date()
        #             dates = [
        #                 today,
        #                 today + datetime.timedelta(days=1),
        #                 today + datetime.timedelta(days=2),
        #                 today + datetime.timedelta(days=3),
        #                 today + datetime.timedelta(days=4),
        #                 today + datetime.timedelta(days=5),
        #             ]
        #
        #             update_menus(None, 'cmi', dates=dates)
        #         except Exception as e:
        #             bot.notify_error(e)
        #
        #             get_app().logger.exception(e)

    def trigger_received(self, trigger: triggers.Trigger):
        with self.lock:  # TODO: Maybe only lock on critical sections?
            app = get_app()
            print('Komidabot received a trigger: {}'.format(type(trigger).__name__), flush=True)
            print(repr(trigger), flush=True)

            if isinstance(trigger, triggers.SubscriptionTrigger):
                dispatch_daily_menus(trigger)
                return

            if triggers.AtAdminAspect in trigger:
                return  # Don't process messages targeted at the admin

            locale = None

            # XXX: Disabled once more because responses aren't reliably in the language the user expects it to be
            # if triggers.LocaleAspect in trigger and trigger[triggers.LocaleAspect].confidence > 0.9:
            #     locale = trigger[triggers.LocaleAspect].locale

            if triggers.SenderAspect in trigger:
                sender = trigger[triggers.SenderAspect].sender
                campuses = Campus.get_active()

                if locale is None:
                    locale = sender.get_locale()

                # TODO: Is this really how we want to handle input?
                if isinstance(trigger, triggers.TextTrigger):
                    text = trigger.text
                    split = text.lower().split(' ')

                    if sender.is_admin():
                        if split[0] == 'setup':
                            recreate_db()
                            create_standard_values()
                            import_dump(app.config['DUMP_FILE'])
                            sender.send_message(messages.TextMessage(trigger, 'Setup done'))
                            return
                        elif split[0] == 'update':
                            sender.send_message(messages.TextMessage(trigger, 'Updating menus...'))
                            update_menus(trigger, *split[1:])
                            sender.send_message(messages.TextMessage(trigger, 'Done updating menus...'))
                            return
                        elif split[0] == 'psid':  # TODO: Deprecated?
                            sender.send_message(messages.TextMessage(trigger, 'Your ID is {}'.format(sender.id.id)))
                            return

                    # TODO: Allow users to send more manual commands
                    if split[0] == 'help':
                        msg = localisation.REPLY_INSTRUCTIONS(locale).format(
                            campuses=', '.join([campus.short_name.lower() for campus in campuses])
                        )
                        sender.send_message(messages.TextMessage(trigger, msg))
                        return

                requested_dates = []
                default_date = False

                if triggers.DatetimeAspect in trigger:
                    date_times = trigger[triggers.DatetimeAspect]
                    requested_dates, invalid_date = nlp_dates.extract_days(
                        date_times)  # TODO: Date parsing needs improving

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
                    for campus in campuses:
                        # FIXME: This should use keywords instead of the short name
                        if trigger.text.lower().count(campus.short_name) > 0:
                            requested_campuses.append(campus)

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

                closed = ClosingDays.find_is_closed(campus, date)

                if closed:
                    # FIXME: Translations need to be moved to a different file
                    translation = komidabot.menu.get_translated_text(closed.translatable, locale)

                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NO_MENU(locale)
                                                             .format(campus=campus.short_name.upper(), date=str(date))))
                    sender.send_message(messages.TextMessage(trigger, translation.translation))
                    return

                menu = komidabot.menu.prepare_menu_text(campus, date, locale)

                if menu is None:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NO_MENU(locale)
                                                             .format(campus=campus.short_name.upper(), date=str(date))))
                else:
                    sender.send_message(messages.TextMessage(trigger, menu))

                # XXX: Disabled experiment
                # if default_date and default_campus and isinstance(trigger, triggers.TextTrigger):
                #     for keyword in ['lunch', 'menu', 'komida']:
                #         if keyword.lower() in trigger.text.lower():
                #             break
                #     else:
                #         sender.send_message(messages.TextMessage(trigger, localisation.REPLY_USE_AT_ADMIN(locale)))

    def notify_error(self, error: Exception):
        with self.lock:
            if self._handling_error:
                # Already handling an error, or we failed handling the previous error, so don't try handling more
                return
            self._handling_error = True

            app = get_app()

            for admin in app.admin_ids:  # type: users.UserId
                user = app.user_manager.get_user(admin)

                user.send_message(messages.TextMessage(triggers.Trigger(),
                                                       '⚠️ An internal error occurred, '
                                                       'please check the console for more information'))

            self._handling_error = False


def dispatch_daily_menus(trigger: triggers.SubscriptionTrigger):
    date = trigger.date or datetime.datetime.now().date()
    day = Day(date.isoweekday())

    # print('Sending out subscription for {} ({})'.format(date, day.name), flush=True)

    user_manager = get_app().user_manager  # type: users.UserManager
    subscribed_users = user_manager.get_subscribed_users(day)
    subscriptions = dict()  # type: Dict[Campus, Dict[str, List[users.User]]]

    for user in subscribed_users:
        if get_app().config.get('DISABLED') and not user.is_admin():
            continue

        if not user.is_feature_active('menu_subscription'):
            # print('User {} not eligible for subscription'.format(user.id), flush=True)
            continue

        subscription = user.get_subscription_for_day(date)
        if subscription is None:
            continue
        if not subscription.active:
            continue

        campus = subscription.campus

        language = user.get_locale() or 'nl_BE'

        if campus not in subscriptions:
            subscriptions[campus] = dict()

        if language not in subscriptions[campus]:
            subscriptions[campus][language] = list()

        subscriptions[campus][language].append(user)

    for campus, languages in subscriptions.items():
        for language, sub_users in languages.items():
            # print('Preparing menu for {} in {}'.format(campus.short_name, language), flush=True)

            closed = ClosingDays.find_is_closed(campus, date)

            if closed:
                continue  # Campus closed, no daily menu

            menu = komidabot.menu.prepare_menu_text(campus, date, language)
            if menu is None:
                continue

            for user in sub_users:
                # print('Sending menu for {} in {} to {}'.format(campus.short_name, language, user.id),
                #       flush=True)
                user.send_message(messages.TextMessage(trigger, menu))


def update_menus(initiator: 'Optional[triggers.Trigger]', *campuses: str, dates: 'List[datetime.date]' = None):
    campus_list = Campus.get_active()

    for campus in campus_list:
        if len(campuses) > 0 and campus.short_name not in campuses:
            continue

        if campus.external_id:
            fetcher = external_menu.ExternalMenu()

            if not dates:
                today = datetime.datetime.today().date()
                dates = [
                    today + datetime.timedelta(days=1),
                    today + datetime.timedelta(days=2),
                    today + datetime.timedelta(days=3),
                    today + datetime.timedelta(days=4),
                    today + datetime.timedelta(days=5),
                    today + datetime.timedelta(days=6),
                    today + datetime.timedelta(days=7),
                ]

            for date in dates:
                if date.isoweekday() in [6, 7]:
                    continue
                fetcher.add_to_lookup(campus, date)

            result = fetcher.lookup_menus()

            for (_, date), items in result.items():
                if len(items) > 0:
                    menu = Menu.get_menu(campus, date)

                    if menu is not None:
                        menu.clear()
                    else:
                        menu = Menu.create(campus, date)

                    for item in items:
                        translatable, translation = Translatable.get_or_create(item.get_combined_text(), 'nl_NL')

                        menu.add_menu_item(translatable, item.food_type, item.get_student_price(),
                                           item.get_staff_price())

        else:
            # TODO: The other campuses are soon using the new system, so this code will be removed once this happens
            scraper = menu_scraper.MenuScraper(campus)

            scraper.find_pdf_location()

            if not scraper.pdf_location:
                if initiator:
                    if triggers.SenderAspect in initiator:
                        message = 'No menu has been found for {}'.format(campus.short_name.upper())
                        initiator[triggers.SenderAspect].sender.send_message(messages.TextMessage(initiator, message))
                continue

            # initiator.send_text_message('Campus {}\n{}'.format(campus.name, scraper.pdf_location))

            scraper.download_pdf()
            scraper.generate_pictures()

            handle_parsed_menu(campus, scraper.parse_pdf())

            # for result in parse_result.parse_results:
            #     print('{}/{}: {} ({})'.format(result.day.name, result.food_type.name, result.name, result.price),
            #           flush=True)

    db.session.commit()


# TODO: Deprecated once each campus changes to the new system
def handle_parsed_menu(campus: Campus, document: menu_scraper.ParsedDocument):
    for day in range(document.start_date.toordinal(), document.end_date.toordinal() + 1):
        date = datetime.date.fromordinal(day)

        menu = Menu.get_menu(campus, date)

        if menu is not None:
            menu.clear()
        else:
            menu = Menu.create(campus, date)

        day_menu: List[menu_scraper.ParseResult] = [result for result in document.parse_results
                                                    if result.day.value == date.isoweekday()
                                                    or result.day == menu_scraper.FrameDay.WEEKLY]

        for item in day_menu:
            if item.name == '':
                continue
            if item.price == '':
                continue

            prices = menu_scraper.parse_price(item.price)

            if prices is None:
                continue  # No price parsed

            prices[0] = Decimal(prices[0].replace('€', '').replace(',', '.').strip())
            prices[1] = Decimal(prices[1].replace('€', '').replace(',', '.').strip())

            translatable, translation = Translatable.get_or_create(item.name, 'nl_NL')
            if item.food_type == menu_scraper.FrameFoodType.SOUP:
                food_type = FoodType.SOUP
            elif item.food_type == menu_scraper.FrameFoodType.VEGAN:
                food_type = FoodType.VEGAN
            elif item.food_type == menu_scraper.FrameFoodType.MEAT:
                food_type = FoodType.MEAT
            elif item.food_type == menu_scraper.FrameFoodType.GRILL:
                food_type = FoodType.GRILL
            else:
                continue

            print((translatable, food_type, prices[0], prices[1]), flush=True)

            menu.add_menu_item(translatable, food_type, prices[0], prices[1])
