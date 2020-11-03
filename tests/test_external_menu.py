import glob
import json
import os
import re
from typing import Any, Dict, List, Union

import yaml
from jsonschema import Draft7Validator

import komidabot.external_menu as external_menu
import komidabot.models as models
from extensions import db
from tests.base import BaseTestCase, HttpCapture


def filter_meta(value: Union[List[Any], Dict[str, Any]]):
    if isinstance(value, dict):
        for key in list(value.keys()):
            if key.startswith('$'):
                del value[key]
            else:
                filter_meta(value[key])
    elif isinstance(value, list):
        for item in value:
            filter_meta(item)


class TestExternalMenu(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.campuses = {
            'cst': models.Campus.create('Stadscampus', 'cst', ['stad', 'stadscampus'], 1),
            'cde': models.Campus.create('Campus Drie Eiken', 'cde', ['drie', 'eiken'], 2),
            'cmi': models.Campus.create('Campus Middelheim', 'cmi', ['middelheim'], 3),
            'cgb': models.Campus.create('Campus Groenenborger', 'cgb', ['groenenborger'], 4),
            'cmu': models.Campus.create('Campus Mutsaard', 'cmu', ['mutsaard'], 5),
            'hzs': models.Campus.create('Hogere Zeevaartschool', 'hzs', ['hogere', 'zeevaartschool'], 6),
        }

        db.session.commit()

        self.assertEqual(self.campuses['cst'].id, 1)

        self.validator_raw = TestExternalMenu.create_validator('raw.schema.json')
        self.validator_parsed = TestExternalMenu.create_validator('parsed.schema.json')
        self.validator_processed = TestExternalMenu.create_validator('processed.schema.json')

    @staticmethod
    def create_validator(schema):
        with open(os.path.join(os.path.dirname(__file__), 'external_menus', schema)) as f:
            schema = json.load(f)

        Draft7Validator.check_schema(schema)
        return Draft7Validator(schema)

    def test_saved_requests(self):
        saved_files = glob.glob(os.path.join(os.path.dirname(__file__), 'external_menus', '*.raw.json'))

        self.maxDiff = 5000

        old_convert_price = external_menu._convert_price

        # conversion_table = {}

        def _convert_price(price_students):
            price_students = str(price_students)

            # nonlocal conversion_table
            #
            # if price_students in conversion_table:
            #     return conversion_table[price_students]
            #
            # conversion_table[price_students] = old_convert_price(price_students)
            #
            # return conversion_table[price_students]

            return {
                '3.20': '4.00',  # external ID 1
                '3.40': '4.20',  # external ID 2
                '3.60': '4.50',  # external ID 3
                '3.80': '4.70',  # external ID 4
                '4.00': '5.00',  # external ID 5
                '4.20': '5.20',  # external ID 6
                '4.40': '5.50',  # external ID 7
                '4.60': '5.70',  # external ID 8
                '4.80': '6.00',  # external ID 9
                '5.00': '6.20',  # external ID 10
                '5.20': '6.50',  # external ID 11
                '5.40': '6.70',  # external ID 12
                '5.60': '7.00',  # external ID 13
            }.get(price_students, price_students)

        external_menu._convert_price = _convert_price

        for saved_file in sorted(saved_files):
            with HttpCapture():  # Ensure no requests are made
                with self.subTest(file=os.path.basename(saved_file)):
                    with self.app.app_context():
                        parsed_out = re.sub(r'raw\.json$', 'parsed.yaml', saved_file)
                        parsed_expected = re.sub(r'raw\.json$', 'parsed.expected.yaml', saved_file)
                        processed_out = re.sub(r'raw\.json$', 'processed.yaml', saved_file)
                        processed_expected = re.sub(r'raw\.json$', 'processed.expected.yaml', saved_file)

                        with open(saved_file, 'r') as f:
                            data_raw = json.load(f)

                        self.validator_raw.validate(data_raw)

                        data_parsed = external_menu.parse_fetched(data_raw)

                        with open(parsed_out, 'w') as f:
                            yaml.safe_dump(data_parsed, f, indent=2)

                        if os.path.exists(parsed_expected):
                            with open(parsed_expected, 'r') as f:
                                data_parsed_expected = yaml.safe_load(f)

                            filter_meta(data_parsed_expected)

                            self.assertEqual(yaml.safe_dump(data_parsed_expected), yaml.safe_dump(data_parsed))

                            # If we already know what is expected, this file will contain the same contents and as such
                            # we do not need to keep it around
                            os.remove(parsed_out)

                        self.validator_parsed.validate(data_parsed)

                        data_processed = external_menu.process_parsed(data_parsed)

                        with open(processed_out, 'w') as f:
                            yaml.safe_dump(data_processed, f, indent=2)

                        if os.path.exists(processed_expected):
                            with open(processed_expected, 'r') as f:
                                data_processed_expected = yaml.safe_load(f)

                            filter_meta(data_processed_expected)

                            self.assertEqual(yaml.safe_dump(data_processed_expected), yaml.safe_dump(data_processed))

                            # If we already know what is expected, this file will contain the same contents and as such
                            # we do not need to keep it around
                            os.remove(processed_out)

                        self.validator_processed.validate(data_processed)

                        # Try and update the menu, this shouldn't cause any issues really.
                        # However we won't check if this was added properly to the database,
                        # different tests should cover this
                        external_menu.update_menu(data_processed)

        external_menu._convert_price = old_convert_price
