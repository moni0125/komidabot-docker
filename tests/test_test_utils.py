import unittest

import tests.utils as utils
from tests.base import BaseTestCase


class TestConstants(BaseTestCase):
    def test_days(self):
        self.assertEqual(utils.DAYS['MON'].isoweekday(), 1, 'Date is not a Monday')
        self.assertEqual(utils.DAYS['TUE'].isoweekday(), 2, 'Date is not a Tuesday')
        self.assertEqual(utils.DAYS['WED'].isoweekday(), 3, 'Date is not a Wednesday')
        self.assertEqual(utils.DAYS['THU'].isoweekday(), 4, 'Date is not a Thursday')
        self.assertEqual(utils.DAYS['FRI'].isoweekday(), 5, 'Date is not a Friday')
        self.assertEqual(utils.DAYS['SAT'].isoweekday(), 6, 'Date is not a Saturday')
        self.assertEqual(utils.DAYS['SUN'].isoweekday(), 7, 'Date is not a Sunday')

    def test_days_list(self):
        self.assertEqual(utils.DAYS_LIST[0].isoweekday(), 1, 'Date is not a Monday')
        self.assertEqual(utils.DAYS_LIST[1].isoweekday(), 2, 'Date is not a Tuesday')
        self.assertEqual(utils.DAYS_LIST[2].isoweekday(), 3, 'Date is not a Wednesday')
        self.assertEqual(utils.DAYS_LIST[3].isoweekday(), 4, 'Date is not a Thursday')
        self.assertEqual(utils.DAYS_LIST[4].isoweekday(), 5, 'Date is not a Friday')
        self.assertEqual(utils.DAYS_LIST[5].isoweekday(), 6, 'Date is not a Saturday')
        self.assertEqual(utils.DAYS_LIST[6].isoweekday(), 7, 'Date is not a Sunday')


if __name__ == '__main__':
    unittest.main()
