import datetime
import unittest

import komidabot.triggers as triggers
from tests.base import BaseTestCase
from tests.users_stub import UserManager as TestUserManager


class TestTriggers(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_manager = TestUserManager()
        self.user1 = self.user_manager.add_user('user1')

        self.triggers = [
            (triggers.Trigger, (), {}),
            (triggers.TextTrigger, ('Hello world!',), {}),
            (triggers.SubscriptionTrigger, (), {}),
            (triggers.SubscriptionTrigger, (), {'date': datetime.date(1999, 12, 31)}),
        ]

        self.aspects = [
            (triggers.SenderAspect, (self.user1,), {}),
            (triggers.DatetimeAspect, ('1999-12-31T00:00:00.000+01:00', 'day',), {}),
            (triggers.LocaleAspect, ('nl_XX', 1.0,), {}),
        ]

    def test_simple_trigger_constructors(self):
        # Test constructors of Trigger and classes extending Trigger without any Aspects

        for TriggerType, args, kwargs in self.triggers:
            TriggerType(*args, **kwargs)

    def test_trigger_constructors_with_aspects(self):
        # Test constructors of Trigger and classes extending Trigger with Aspects
        pass

        # for TriggerType, args, kwargs in self.triggers:
        #     TriggerType(*args, **kwargs)

    def test_aspect_constructors(self):
        # Test constructors of classes extending Aspect

        for AspectType, args, kwargs in self.aspects:
            AspectType(*args, **kwargs)

    def test_simple_extend(self):
        # Test the extend method of Trigger and classes extending Trigger without any Aspects

        trigger = triggers.Trigger()
        self.assertIsInstance(trigger, triggers.Trigger)

        for TriggerType, args, kwargs in self.triggers:
            trigger = TriggerType.extend(trigger, *args, **kwargs)
            self.assertIsInstance(trigger, TriggerType)

    def test_extend_with_aspects(self):
        # Test the extend method of Trigger and classes extending Trigger with Aspects
        pass

        # trigger = triggers.Trigger()
        # self.assertIsInstance(trigger, triggers.Trigger)
        #
        # for TriggerType, args, kwargs in self.triggers:
        #     trigger = TriggerType.extend(trigger, *args, **kwargs)
        #     self.assertIsInstance(trigger, TriggerType)

    def test_no_aspects(self):
        # Test that the 'in' operator does not falsely report Aspects inside Triggers

        for TriggerType, args, kwargs in self.triggers:
            trigger = TriggerType(*args, **kwargs)

            self.assertNotIn(triggers.Aspect, trigger)
            self.assertNotIn(triggers.SenderAspect, trigger)
            self.assertNotIn(triggers.DatetimeAspect, trigger)
            self.assertNotIn(triggers.LocaleAspect, trigger)

    def test_single_aspect(self):
        # Test that the 'in' operator does not falsely report Aspects inside Triggers if there is another type

        for TriggerType, args, kwargs in self.triggers:
            for AspectType, args2, kwargs2 in self.aspects:
                aspect = AspectType(*args2, **kwargs2)
                trigger = TriggerType(*args, aspects=[aspect, ], **kwargs)

                self.assertIn(AspectType, trigger)
                self.assertEqual(trigger[AspectType], [aspect, ] if AspectType.allows_multiple else aspect)

                for AspectType2, _, _ in self.aspects:
                    if AspectType2 is AspectType:
                        continue  # This is the type we're testing in this instance

                    self.assertNotIn(AspectType2, trigger)

    def test_multiple_aspects(self):
        # Test that the 'in' operator does not falsely report Aspects not inside Triggers if there are others as well

        for TriggerType, args, kwargs in self.triggers:
            for AspectType, args2, kwargs2 in self.aspects:
                for AspectType2, args3, kwargs3 in self.aspects:
                    if AspectType is AspectType2:
                        continue  # This Aspect type is already in the Trigger

                    aspect1 = AspectType(*args2, **kwargs2)
                    aspect2 = AspectType2(*args3, **kwargs3)
                    trigger = TriggerType(*args, aspects=[aspect1, aspect2, ], **kwargs)

                    self.assertIn(AspectType, trigger)
                    self.assertEqual(trigger[AspectType], [aspect1, ] if AspectType.allows_multiple else aspect1)
                    self.assertIn(AspectType2, trigger)
                    self.assertEqual(trigger[AspectType2], [aspect2, ] if AspectType2.allows_multiple else aspect2)

                    for AspectType3, _, _ in self.aspects:
                        if AspectType3 is AspectType3 or AspectType3 is AspectType2:
                            continue  # This is the type we're testing in this instance

                        self.assertNotIn(AspectType3, trigger)


if __name__ == '__main__':
    unittest.main()
