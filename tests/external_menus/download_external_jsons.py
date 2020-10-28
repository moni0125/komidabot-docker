import datetime
import json
import os
import sys
import time
from collections import deque
from datetime import datetime, timedelta

import requests
from jsonschema import ValidationError, Draft7Validator

BASE_ENDPOINT = 'https://restickets.uantwerpen.be/'
MENU_API = '{endpoint}api/GetMenuByDate/{campus}/{date}'

FILE_LOCATION = '{date}_{campus}.raw.json'

API_GET_HEADERS = dict()
API_GET_HEADERS['Accept'] = 'application/json'

campuses = {
    'cst': 1,
    'cde': 2,
    'cmi': 3,
    'cgb': 4,
    'cmu': 5,
    'hzs': 6,
}


class Limiter:
    def __init__(self, max_rate: int):
        self.max_rate = max_rate
        self.last_times = deque()

    def __call__(self):
        now = datetime.now()

        if len(self.last_times) < self.max_rate:
            self.last_times.append(now)
            return

        delta = (now - self.last_times.popleft()).total_seconds()

        if delta < 1:
            time.sleep(1.0 - delta)

        self.last_times.append(now)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        do_requests = True
    elif len(sys.argv) == 4:
        do_requests = (sys.argv[3] != '0')
    else:
        print('Needs 2 parameters: first date and last date. Optionally 3rd parameter 0/1', file=sys.stderr)
        sys.exit(1)

    first = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
    last = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()

    session = requests.Session()
    limiter = Limiter(5)

    with open('raw.schema.json') as f:
        schema = json.load(f)

    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)

    violations = []

    for date in (first + timedelta(days=x) for x in range(0, (last - first).days + 1)):
        date: datetime.date

        if date.isoweekday() > 5:  # No weekends
            continue

        print('Date:', date, file=sys.stderr)

        for campus, campus_id in campuses.items():
            print('- Campus:', campus, file=sys.stderr)

            url = MENU_API.format(endpoint=BASE_ENDPOINT, campus=campus_id, date=date.strftime('%Y-%m-%d'))
            file = FILE_LOCATION.format(campus=campus, date=date.strftime('%Y-%m-%d'))

            if os.path.isfile(file):
                print('  Exists', file=sys.stderr)

                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                except json.decoder.JSONDecodeError:
                    print('! Json decode error', file=sys.stderr)
                    continue

                try:
                    validator.validate(data)
                except ValidationError as e:
                    print('! Schema validation failed: ', e, file=sys.stderr)

                    violations.append((date, campus))
            elif do_requests:
                limiter()

                response = session.get(url, headers=API_GET_HEADERS)
                if 400 <= response.status_code < 500:
                    print('  Client error on HTTP request', file=sys.stderr)
                    continue
                if 500 <= response.status_code < 600:
                    print('  Server error on HTTP request', file=sys.stderr)
                    continue

                if response.status_code == 204:
                    print('  No response', file=sys.stderr)
                    continue

                print('  Response:', response, file=sys.stderr)

                try:
                    data = json.loads(response.text)
                except json.decoder.JSONDecodeError:
                    print('! Json decode error: ', response.text, file=sys.stderr)
                    continue

                data['$schema'] = './raw.schema.json'

                try:
                    validator.validate(data)
                except ValidationError as e:
                    print('! Schema validation failed: ', e, file=sys.stderr)

                    violations.append((date, campus))

                with open(file, 'w') as f:
                    json.dump(data, f, indent=2)

    print('Violations:')
    for violation in violations:
        print(violation)
