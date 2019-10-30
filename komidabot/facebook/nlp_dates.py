from typing import List

import dateutil.parser as date_parser

import komidabot.triggers as triggers
from komidabot.facebook.received_message import NLPAttribute


# TODO: Deprecated
def extract_days_legacy(date_attributes: List[NLPAttribute]):
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
        else:
            invalid_date = True

    return dates, invalid_date


def extract_days(aspects: List[triggers.DatetimeAspect]):
    dates = []
    invalid_date = False

    for attribute in aspects:
        grain = attribute.grain
        value = attribute.value

        if grain is None or value is None:
            continue

        # TODO: Date parsing could be a lot better
        # Ex. vanmiddag is rejected

        if grain == 'day':
            date = date_parser.isoparse(value).date()
            dates.append(date)
        else:
            invalid_date = True

    return dates, invalid_date
