import datetime, threading
from typing import List, Optional

from flask import current_app as app

from komidabot.bot import Bot, ReceivedTextMessage
from komidabot.facebook.messenger import MessageSender
import komidabot.facebook.nlp_dates as nlp_dates
from komidabot.conversation_manager import ConversationManager as LegacyConversationManager
import komidabot.menu
from komidabot.menu_scraper import FrameFoodType, MenuScraper, ParseResult, parse_price
import komidabot.triggers as triggers

from komidabot.models import Campus, Day, FoodType, Menu, Subscription, Translatable
from komidabot.models import create_standard_values, import_dump, recreate_db

from extensions import db


# TODO: Bot should not be part of the facebook package
class Komidabot(Bot):
    def __init__(self):
        self.lock = threading.Lock()
        # TODO: Deprecated
        self.legacy_conversation_manager = LegacyConversationManager()

    # TODO: Deprecated
    def message_received_legacy(self, message: ReceivedTextMessage):
        with self.lock:
            print('Komidabot received a legacy message', flush=True)

            # TODO: It may be an idea to keep track of active conversations
            # Simple requests to get the menu would then be conversations that end immediately
            # - Initial setup -> ask user some basic questions to get started
            # - ADMIN: Weekly menu, confirm the menu for each day/campus
            # - ADMIN: Updating configuration values

            # TODO: This REALLY shouldn't be part of the facebook package
            if self.legacy_conversation_manager.handle_message_conversation(message):
                return

            if message.sender.is_admin():
                if message.text == 'setup':
                    recreate_db()
                    create_standard_values()
                    import_dump(app.config['DUMP_FILE'])
                    message.sender.send_text_message('Setup done')
                    return
                elif message.text == 'update':
                    message.sender.send_text_message('Updating menus...')
                    self.update_menus(message.sender)
                    message.sender.send_text_message('Done updating menus...')
                    return
                elif message.text == 'psid':
                    message.sender.send_text_message('Your ID is {}'.format(message.sender.get_id()))
                    return
                elif message.text == 'test':
                    # Conversation.initiate_conversation(MenuConfirmationConversation(message.sender, None), message)
                    return

            # TODO: This requires some modifications
            dates, invalid_date = nlp_dates.extract_days(message.get_attributes('datetime'))

            if invalid_date:
                message.sender.send_text_message('Sorry, I am unable to understand some of the entered dates')

            if len(dates) == 0:
                dates.append(datetime.datetime.now().date())

            if len(dates) > 3:
                message.sender.send_text_message('Sorry, please ask for at most 3 days')
                return

            campuses = Campus.get_active()
            requested_campuses = []

            for campus in campuses:
                if message.text.lower().count(campus.short_name) > 0:
                    requested_campuses.append(campus)

            subscription = Subscription.find_by_facebook_id(message.sender.get_id())

            for date in dates:
                if len(requested_campuses) == 0:
                    if subscription is not None:
                        campus = subscription.get_campus(Day(date.isoweekday()))
                    if campus is None:
                        campus = Campus.get_by_short_name('cmi')
                elif len(requested_campuses) > 1:
                    message.sender.send_text_message('Sorry, please only ask for a single campus at a time')
                    return
                else:
                    campus = requested_campuses[0]

                menu = komidabot.menu.prepare_menu_text(campus, date, message.sender.get_locale())

                if menu is None:
                    message.sender.send_text_message('Sorry, no menu has been found for {} on {}'
                                                     .format(campus.short_name.upper(), str(date)))
                else:
                    message.sender.send_text_message(menu)

    def trigger_received(self, trigger: triggers.Trigger):
        with self.lock:  # TODO: Maybe only lock on critical sections?
            print('Komidabot received a trigger: {}'.format(type(trigger.__name__)), flush=True)

            if isinstance(trigger, triggers.UserTrigger):
                pass  # Handle trigger

            if isinstance(trigger, triggers.SubscriptionTrigger):
                pass  # TODO: Gather all subscribed users and send messages

    # noinspection PyMethodMayBeStatic
    def update_menus(self, initiator: 'Optional[MessageSender]'):
        # TODO: Store a hash of the source file for each menu to check for changes
        campus_list = Campus.get_active()

        for campus in campus_list:
            scraper = MenuScraper(campus)

            scraper.find_pdf_location()

            # initiator.send_text_message('Campus {}\n{}'.format(campus.name, scraper.pdf_location))

            scraper.download_pdf()
            scraper.generate_pictures()
            parse_result = scraper.parse_pdf()

            for day in range(parse_result.start_date.toordinal(), parse_result.end_date.toordinal() + 1):
                date = datetime.date.fromordinal(day)

                menu = Menu.get_menu(campus, date)

                if menu is not None:
                    menu.delete(commit=False)

                menu = Menu.create(campus, date, commit=False)

                day_menu: List[ParseResult] = [result for result in parse_result.parse_results
                                               if result.day.value == date.isoweekday()
                                               or result.food_type == FrameFoodType.GRILL]
                # if result.day.value == date.isoweekday() or result.day.value == -1]
                # TODO: Fix pasta!
                # TODO: Fix grill stadscampus -> meerdere grills op een week

                for item in day_menu:
                    if item.name == '':
                        continue
                    if item.price == '':
                        continue

                    prices = parse_price(item.price)

                    if prices is None:
                        continue  # No price parsed

                    translatable, translation = Translatable.get_or_create(item.name, 'nl_NL', commit=False)
                    if item.food_type == FrameFoodType.SOUP:
                        food_type = FoodType.SOUP
                    elif item.food_type == FrameFoodType.VEGAN:
                        food_type = FoodType.VEGAN
                    elif item.food_type == FrameFoodType.MEAT:
                        food_type = FoodType.MEAT
                    elif item.food_type == FrameFoodType.GRILL:
                        food_type = FoodType.GRILL
                    else:
                        continue  # TODO: Fix pasta!

                    print((translatable, food_type, prices[0], prices[1]), flush=True)

                    menu.add_menu_item(translatable, food_type, prices[0], prices[1], commit=False)

            db.session.commit()

            # for result in parse_result.parse_results:
            #     print('{}/{}: {} ({})'.format(result.day.name, result.food_type.name, result.name, result.price),
            #           flush=True)
