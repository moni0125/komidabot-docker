import atexit
import datetime
import threading
from typing import Dict, List, Optional, Union

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import komidabot.facebook.nlp_dates as nlp_dates
import komidabot.localisation as localisation
import komidabot.menu
import komidabot.menu_scraper as menu_scraper
import komidabot.messages as messages
import komidabot.triggers as triggers
import komidabot.users as users
from extensions import db
from komidabot.app import get_app
from komidabot.bot import Bot, ReceivedTextMessage
from komidabot.facebook.messenger import MessageSender
from komidabot.models import Campus, ClosingDays, Day, FoodType, Menu, AppUser, Translatable
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
                bot.trigger_received(triggers.SubscriptionTrigger())

        # FIXME: This is disabled for now
        # @self.scheduler.scheduled_job(CronTrigger(hour=1, minute=0, second=0),  # Run every day to find changes
        #                               args=(the_app.app_context, self),
        #                               id='menu_update', name='Daily late-night update of the menus')
        # def menu_update(context, bot: 'Komidabot'):
        #     with context():
        #         bot.update_menus(None)

    # TODO: Deprecated
    def message_received_legacy(self, message: ReceivedTextMessage):
        with self.lock:
            print('Komidabot received a legacy message', flush=True)

            if message.sender.is_admin():
                if message.text == 'setup':
                    recreate_db()
                    create_standard_values()
                    import_dump(get_app().config['DUMP_FILE'])
                    message.sender.send_text_message('Setup done')
                    return
                elif message.text == 'update':
                    message.sender.send_text_message('Updating menus...')
                    update_menus(message.sender)
                    message.sender.send_text_message('Done updating menus...')
                    return
                elif message.text == 'psid':
                    message.sender.send_text_message('Your ID is {}'.format(message.sender.get_id()))
                    return

            # TODO: This requires some modifications
            dates, invalid_date = nlp_dates.extract_days_legacy(message.get_attributes('datetime'))

            if invalid_date:
                message.sender.send_text_message('Sorry, I am unable to understand some of the entered dates')

            if len(dates) == 0:
                dates.append(datetime.datetime.now().date())

            if len(dates) > 1:
                message.sender.send_text_message('Sorry, please request only a single day')
                return

            campuses = Campus.get_active()
            requested_campuses = []

            for campus in campuses:
                if message.text.lower().count(campus.short_name) > 0:
                    requested_campuses.append(campus)

            user = AppUser.find_by_facebook_id(message.sender.get_id())

            for date in dates:
                day = Day(date.isoweekday())

                if day == Day.SATURDAY or day == Day.SUNDAY:
                    message.sender.send_text_message(localisation.REPLY_WEEKEND(message.sender.get_locale()))
                    continue

                if len(requested_campuses) == 0:
                    if user is not None:
                        campus = user.get_campus(day)
                    if campus is None:
                        campus = Campus.get_by_short_name('cmi')
                elif len(requested_campuses) > 1:
                    message.sender.send_text_message('Sorry, please only ask for a single campus at a time')
                    continue
                else:
                    campus = requested_campuses[0]

                closed = ClosingDays.find_is_closed(campus, date)

                if closed:
                    translation = komidabot.menu.get_translated_text(closed.translatable, message.sender.get_locale())

                    message.sender.send_text_message(localisation.REPLY_NO_MENU(message.sender.get_locale())
                                                     .format(campus.short_name.upper(), str(date)))
                    message.sender.send_text_message(translation.translation)
                    return

                menu = komidabot.menu.prepare_menu_text(campus, date, message.sender.get_locale() or 'nl_BE')

                if menu is None:
                    message.sender.send_text_message(localisation.REPLY_NO_MENU(message.sender.get_locale())
                                                     .format(campus.short_name.upper(), str(date)))
                else:
                    message.sender.send_text_message(menu)

    def trigger_received(self, trigger: triggers.Trigger):
        with self.lock:  # TODO: Maybe only lock on critical sections?
            app = get_app()
            print('Komidabot received a trigger: {}'.format(type(trigger).__name__), flush=True)
            print(repr(trigger), flush=True)

            locale = None
            if triggers.LocaleAspect in trigger:
                locale = trigger[triggers.LocaleAspect].locale

            if triggers.SenderAspect in trigger:
                sender = trigger[triggers.SenderAspect].sender

                if locale is None:
                    locale = sender.get_locale()

                # TODO: Is this really how we want to handle input?
                if isinstance(trigger, triggers.TextTrigger) and sender.is_admin():
                    text = trigger.text
                    if text == 'setup':
                        recreate_db()
                        create_standard_values()
                        import_dump(app.config['DUMP_FILE'])
                        sender.send_message(messages.TextMessage(trigger, 'Setup done'))
                        return
                    elif text == 'update':
                        sender.send_message(messages.TextMessage(trigger, 'Updating menus...'))
                        update_menus(trigger)
                        sender.send_message(messages.TextMessage(trigger, 'Done updating menus...'))
                        return
                    elif text == 'fix':
                        sender.send_message(messages.TextMessage(trigger, 'Applying fixes'))
                        apply_menu_fixes()
                        sender.send_message(messages.TextMessage(trigger, 'Done applying fixes...'))
                        return
                    elif text == 'psid':  # TODO: Deprecated?
                        sender.send_message(messages.TextMessage(trigger, 'Your ID is {}'.format(sender.id.id)))
                        return

                # FIXME: This code is an adapted copy of the old path and should be rewritten
                # BEGIN DEPRECATED CODE
                date = None

                if triggers.DatetimeAspect in trigger:
                    date_times = trigger[triggers.DatetimeAspect]
                    dates, invalid_date = nlp_dates.extract_days(date_times)

                    if invalid_date:
                        sender.send_message(messages.TextMessage(trigger, localisation.REPLY_INVALID_DATE(locale)))

                    if len(dates) > 1:
                        sender.send_message(messages.TextMessage(trigger, localisation.REPLY_TOO_MANY_DAYS(locale)))
                        return
                    elif len(dates) == 1:
                        date = dates[0]

                if date is None:
                    date = datetime.datetime.now().date()

                day = Day(date.isoweekday())

                if day == Day.SATURDAY or day == Day.SUNDAY:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_WEEKEND(locale)))
                    return

                campuses = Campus.get_active()
                requested_campuses = []

                if isinstance(trigger, triggers.TextTrigger):
                    for campus in campuses:
                        if trigger.text.lower().count(campus.short_name) > 0:
                            requested_campuses.append(campus)

                if len(requested_campuses) == 0:
                    campus = sender.get_campus_for_day(date)
                    if campus is None:
                        campus = Campus.get_by_short_name('cmi')
                elif len(requested_campuses) > 1:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_TOO_MANY_CAMPUSES(locale)))
                    return
                else:
                    campus = requested_campuses[0]

                closed = ClosingDays.find_is_closed(campus, date)

                if closed:
                    translation = komidabot.menu.get_translated_text(closed.translatable, locale)

                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NO_MENU(locale)
                                                             .format(campus.short_name.upper(), str(date))))
                    sender.send_message(messages.TextMessage(trigger, translation.translation))
                    return

                menu = komidabot.menu.prepare_menu_text(campus, date, locale)

                if menu is None:
                    sender.send_message(messages.TextMessage(trigger, localisation.REPLY_NO_MENU(locale)
                                                             .format(campus.short_name.upper(), str(date))))
                else:
                    sender.send_message(messages.TextMessage(trigger, menu))

                return
                # END DEPRECATED CODE

            if isinstance(trigger, triggers.SubscriptionTrigger):
                date = trigger.date or datetime.datetime.now().date()
                day = Day(date.isoweekday())

                # print('Sending out subscription for {} ({})'.format(date, day.name), flush=True)

                user_manager = get_app().user_manager  # type: users.UserManager
                subscribed_users = user_manager.get_subscribed_users(day)
                subscriptions = dict()  # type: Dict[Campus, Dict[str, List[users.User]]]

                for user in subscribed_users:
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

                        menu = komidabot.menu.prepare_menu_text(campus, date, language)
                        if menu is None:
                            continue

                        for user in sub_users:
                            # print('Sending menu for {} in {} to {}'.format(campus.short_name, language, user.id),
                            #       flush=True)
                            user.send_message(messages.TextMessage(trigger, menu))

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
                                                       'An internal error occurred, '
                                                       'please check the console for more information'))

            self._handling_error = False


def update_menus(initiator: 'Optional[Union[MessageSender, triggers.Trigger]]'):
    session = db.session  # FIXME: Create new session

    # TODO: Store a hash of the source file for each menu to check for changes
    campus_list = Campus.get_active()

    for campus in campus_list:
        scraper = menu_scraper.MenuScraper(campus)

        scraper.find_pdf_location()

        if not scraper.pdf_location:
            message = 'No menu has been found for {}'.format(campus.short_name.upper())
            if isinstance(initiator, MessageSender):
                initiator.send_text_message(message)
                pass
            elif isinstance(initiator, triggers.Trigger):
                if triggers.SenderAspect in initiator:
                    initiator[triggers.SenderAspect].sender.send_message(messages.TextMessage(initiator, message))
            continue

        # initiator.send_text_message('Campus {}\n{}'.format(campus.name, scraper.pdf_location))

        scraper.download_pdf()
        scraper.generate_pictures()

        handle_parsed_menu(campus, scraper.parse_pdf(), session)

        # for result in parse_result.parse_results:
        #     print('{}/{}: {} ({})'.format(result.day.name, result.food_type.name, result.name, result.price),
        #           flush=True)


def handle_parsed_menu(campus: Campus, document: menu_scraper.ParsedDocument, session):
    for day in range(document.start_date.toordinal(), document.end_date.toordinal() + 1):
        date = datetime.date.fromordinal(day)

        menu = Menu.get_menu(campus, date)

        if menu is not None:
            menu.delete(session=session)

        menu = Menu.create(campus, date, session=session)

        day_menu: List[menu_scraper.ParseResult] = [result for result in document.parse_results
                                                    if result.day.value == date.isoweekday()
                                                    or result.day == menu_scraper.FrameDay.WEEKLY]
        # if result.day.value == date.isoweekday() or result.day.value == -1]
        # TODO: Fix pasta!
        # TODO: Fix grill stadscampus -> meerdere grills op een week
        # TODO: This may not be necessary in the near future

        for item in day_menu:
            if item.name == '':
                continue
            if item.price == '':
                continue

            prices = menu_scraper.parse_price(item.price)

            if prices is None:
                continue  # No price parsed

            translatable, translation = Translatable.get_or_create(item.name, 'nl_NL', session=session)
            if item.food_type == menu_scraper.FrameFoodType.SOUP:
                food_type = FoodType.SOUP
            elif item.food_type == menu_scraper.FrameFoodType.VEGAN:
                food_type = FoodType.VEGAN
            elif item.food_type == menu_scraper.FrameFoodType.MEAT:
                food_type = FoodType.MEAT
            elif item.food_type == menu_scraper.FrameFoodType.GRILL:
                food_type = FoodType.GRILL
            else:
                continue  # TODO: Fix pasta!

            print((translatable, food_type, prices[0], prices[1]), flush=True)

            menu.add_menu_item(translatable, food_type, prices[0], prices[1], session=session)

    session.commit()


def apply_menu_fixes():
    session = db.session

    # # Stadscampus
    # campus = Campus.get_by_short_name('cst')
    #
    # # Monday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 28))
    # menu.add_menu_item(Translatable.get_or_create('Kippenbrochette met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,20', '€6,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Steak met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,40', '€6,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met vegetarische bolognaise', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,80', '€4,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met groene curry, gehaktballetjes en munt', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,80', '€4,70', session=session)
    #
    # # Tuesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 29))
    # menu.add_menu_item(Translatable.get_or_create('Kippenbrochette met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,20', '€6,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Steak met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,40', '€6,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met vegetarische bolognaise', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,80', '€4,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met groene curry, gehaktballetjes en munt', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,80', '€4,70', session=session)
    #
    # # Wednesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 30))
    # menu.add_menu_item(Translatable.get_or_create('Kippenbrochette met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,20', '€6,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Steak met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,40', '€6,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met vegetarische bolognaise', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,80', '€4,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met groene curry, gehaktballetjes en munt', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,80', '€4,70', session=session)
    #
    # # Thursday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 31))
    # menu.add_menu_item(Translatable.get_or_create('Kippenbrochette met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,20', '€6,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Steak met portosaus', 'nl_NL', session=session)[0],
    #                    FoodType.GRILL, '€5,40', '€6,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met vegetarische bolognaise', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,80', '€4,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met groene curry, gehaktballetjes en munt', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,80', '€4,70', session=session)
    #
    # # Campus Drie Eiken
    # campus = Campus.get_by_short_name('cde')
    #
    # # Monday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 28))
    # menu.add_menu_item(Translatable.get_or_create('Pasta alfredo met spinazie', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta ricotta met pikante salami', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    #
    # # Tuesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 29))
    # menu.add_menu_item(Translatable.get_or_create('Pasta alfredo met spinazie', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta ricotta met pikante salami', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    #
    # # Wednesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 30))
    # menu.add_menu_item(Translatable.get_or_create('Pasta alfredo met spinazie', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta ricotta met pikante salami', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    #
    # # Thursday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 31))
    # menu.add_menu_item(Translatable.get_or_create('Pasta alfredo met spinazie', 'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta ricotta met pikante salami', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    #
    # # Campus Middelheim
    # campus = Campus.get_by_short_name('cmi')
    #
    # # Monday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 28))
    # menu.add_menu_item(Translatable.get_or_create('Pasta met schorseneren in lookboter met ei, olijven en peultjes',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,40', '€4,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta bolognaise', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Salade met krieltjes, ei en croutons',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.SALAD, '€3,80', '€4,70', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Salade Jambon', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.SALAD, '€5,20', '€6,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Bagel atletico', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.SUB, '€2,30', '', session=session)
    #
    # # Tuesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 29))
    # menu.add_menu_item(Translatable.get_or_create('Knolseldersoep',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.SOUP, '€0,90', '€1,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Oostends vispasteitje met wortelpuree',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.MEAT, '€4,40', '€5,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Paddenstoelencurry met rijst en wortelen',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met schorseneren in lookboter met ei, olijven en peultjes',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,40', '€4,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta bolognaise', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Mixed grill met choronsaus, salad-bar en frieten', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.GRILL, '€5,60', '€7,00', session=session)
    #
    # # Wednesday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 30))
    # menu.add_menu_item(Translatable.get_or_create('Ministrone',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.SOUP, '€0,90', '€1,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Blinde vink met champignonsaus, broccoli en peterselieaardappelen',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.MEAT, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pizza Margherita',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.VEGAN, '€4,00', '€5,00', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met schorseneren in lookboter met ei, olijven en peultjes',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,40', '€4,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta bolognaise', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Mixed grill met choronsaus, salad-bar en frieten', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.GRILL, '€5,60', '€7,00', session=session)
    #
    # # Thursday
    # menu = Menu.get_menu(campus, datetime.date(2019, 10, 31))
    # menu.add_menu_item(Translatable.get_or_create('Bio-pompoensoep',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.SOUP, '€0,90', '€1,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Goulash met spletrisotto',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.MEAT, '€4,40', '€5,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Griekse pasta met paprikaharissa en geitenkaas',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.VEGAN, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta met schorseneren in lookboter met ei, olijven en peultjes',
    #                                               'nl_NL', session=session)[0],
    #                    FoodType.PASTA_VEGAN, '€3,40', '€4,20', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Pasta bolognaise', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.PASTA_MEAT, '€3,60', '€4,50', session=session)
    # menu.add_menu_item(Translatable.get_or_create('Mixed grill met choronsaus, salad-bar en frieten', 'nl_NL',
    #                                               session=session)[0],
    #                    FoodType.GRILL, '€5,60', '€7,00', session=session)

    # document = menu_scraper.ParsedDocument(datetime.date(2019, 10, 28), datetime.date(2019, 10, 31), {})
    # document.add_parse_result(menu_scraper.ParseResult(menu_scraper.FrameDay.MONDAY,
    #                                                    menu_scraper.FrameFoodType.SOUP,
    #                                                    'Wortelsoep',
    #                                                    '€0,90 / €1,20'))
    # document.add_parse_result(menu_scraper.ParseResult(menu_scraper.FrameDay.MONDAY,
    #                                                    menu_scraper.FrameFoodType.VEGAN,
    #                                                    'Bladerdeeg met geitenkaas, een pittig zoet slaatje '
    #                                                    'en frietjes',
    #                                                    '€4,80 / €6,00'))
    # document.add_parse_result(menu_scraper.ParseResult(menu_scraper.FrameDay.MONDAY,
    #                                                    menu_scraper.FrameFoodType.MEAT,
    #                                                    'Kippenoesters, Frieten, Pittig zout slaatje',
    #                                                    '€3,80 / €4,70'))
    # document.add_parse_result(menu_scraper.ParseResult(menu_scraper.FrameDay.MONDAY,
    #                                                    menu_scraper.FrameFoodType.GRILL,
    #                                                    'Mixed grill, Choronsaus, Frieten, Saladbar',
    #                                                    '€5,60 / €7,00'))
    #
    # handle_parsed_menu(Campus.get_by_short_name('cmi'), document, session)

    session.commit()
