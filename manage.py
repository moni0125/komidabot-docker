import os
import signal
import unittest
from typing import Optional

import click
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


@cli.command(with_appcontext=False)
@click.option('--case')
def test(case: Optional[str]):
    """Runs the tests without code coverage"""
    if case:
        tests = unittest.TestLoader().loadTestsFromName('tests.' + case)
    else:
        tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


def handler(signum: int, _):
    if signum == signal.SIGTERM:
        print('Performing shutdown')
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handler)
    cli()
