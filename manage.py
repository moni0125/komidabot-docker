import datetime
import glob
import json
import os
import signal
import unittest
from typing import Optional

import click
from colour_runner.runner import ColourTextTestRunner
from flask import current_app
from flask.cli import FlaskGroup

import komidabot.ipc as ipc
import komidabot.models as models
from app import create_app

cli = FlaskGroup(create_app=create_app)


@cli.command('recreate_db')
def recreate_db():
    models.recreate_db()


@cli.command('seed_db')
def seed_db():
    models.create_standard_values()
    models.import_dump(current_app.config['DUMP_FILE'])


@cli.command('run_subscription')
def run_subscription():
    ipc.send_message({'action': 'sub'})


@cli.command('update_menus')
def update_menus():
    ipc.send_message({'action': 'update_menu'})


@cli.command('cleanup')
def cleanup():
    ipc.send_message({'action': 'cleanup'})


@cli.command('synchronize_menus')
def synchronize_menus():
    ipc.send_message({'action': 'synchronize_menus'})


@cli.command('upload_learning_data')
def upload_learning_data():
    import komidabot.external_menu as external_menu
    from extensions import db
    from komidabot.rate_limit import Limiter

    limiter = Limiter(10)
    files = glob.glob(os.path.join(os.path.dirname(__file__), 'learning-data', '*.json'))

    for file in sorted(files):
        limiter()
        print(os.path.basename(file))

        try:
            with open(file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print('Could not decode:', file)
            continue

        campus = models.Campus.get_by_short_name(data['restaurant'])
        date = datetime.date.fromisoformat(data['date'])

        try:
            data_raw = external_menu.fetch_raw(campus, date)
            data_parsed = external_menu.parse_fetched(data_raw)
            data_processed = external_menu.process_parsed(data_parsed)
        except Exception:
            print('Failure parsing external menu for:', file)
            continue

        reference_menu: list = data['menu']
        processed_menu: list = data_processed['menu'] if data_processed is not None else []

        matched = []

        for reference_item in reference_menu:
            i = 0

            for processed_item in processed_menu:
                if processed_item['name']['nl'].lower() == reference_item['course_name'].lower():
                    matched.append((reference_item, processed_item))
                    break

                i = i + 1
            else:
                print('Could not match reference item', reference_item['course_name'].lower())
                continue

            processed_menu.pop(i)

        for processed_item in processed_menu:
            print('Could not match processed item', processed_item['name']['nl'].lower())

        try:
            for reference_item, processed_item in matched:
                models.LearningDatapoint.create(campus, date, reference_item['screenshot'], processed_item)
        except Exception:
            print('Failure adding to database for', file)
            continue

    db.session.commit()


@cli.command(with_appcontext=False)
@click.option('--case')
def test(case: Optional[str]):
    """Runs the tests without code coverage"""
    if case:
        tests = unittest.TestLoader().loadTestsFromName('tests.' + case)
    else:
        tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = ColourTextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    # This makes Flash return an exit code of 1, otherwise it defaults to 0 even if returning 0
    raise click.exceptions.Exit(1)


def handler(signum: int, _):
    if signum == signal.SIGTERM:
        print('Performing shutdown')
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handler)
    cli()
