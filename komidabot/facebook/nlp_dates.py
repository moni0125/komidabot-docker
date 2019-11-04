from typing import List

import dateutil.parser as date_parser

import komidabot.triggers as triggers


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
