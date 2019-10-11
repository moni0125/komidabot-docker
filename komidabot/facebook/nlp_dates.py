from typing import List
import dateutil.parser as date_parser

from komidabot.facebook.received_message import NLPAttribute


def extract_days(date_attributes: List[NLPAttribute]):
    dates = []
    invalid_date = False

    for attribute in date_attributes:
        grain = attribute.data.get('grain')
        value = attribute.data.get('value')

        if grain is None or value is None:
            continue

        # TODO: Date parsing could be a lot better
        # Ex. vanmiddag is rejected

        if grain == 'day':
            date = date_parser.isoparse(value).date()
            dates.append(date)
            print(date, flush=True)
        else:
            invalid_date = True

    return dates, invalid_date
