import json
import os
import sys
import traceback
from functools import wraps

from flask import jsonify, session, request
from jsonschema import validate, ValidationError
from werkzeug.http import HTTP_STATUS_CODES

from komidabot.app import get_app
from komidabot.debug.state import DebuggableException

__all__ = ['check_logged_in', 'expects_schema', 'is_logged_in', 'wrap_exceptions']


def is_logged_in():
    return session.get('logged_in') is not None


# FIXME: In the future, this should ideally be a proper login system, with a database et al connected to it
def check_logged_in(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        if not is_logged_in():
            return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 200

        return func(*args, **kwargs)

    return decorated_func


def wrap_exceptions(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DebuggableException as e:
            app = get_app()
            app.bot.notify_error(e)

            e.print_info(app.logger)

            return jsonify({'status': 500, 'message': HTTP_STATUS_CODES[500]}), 500
        except Exception as e:
            # noinspection PyBroadException
            try:
                get_app().bot.notify_error(e)
            except Exception:
                pass

            traceback.print_tb(e.__traceback__)
            print(e, flush=True, file=sys.stderr)

            return jsonify({'status': 500, 'message': HTTP_STATUS_CODES[500]}), 500

    return decorated_func


def expects_schema(input_schema: str = None, output_schema: str = None):
    in_schema = None
    if input_schema is not None:
        with open(os.path.join(os.getcwd(), 'schemas', input_schema + '.json')) as f:
            in_schema = json.load(f)

    out_schema = None
    if output_schema is not None:
        with open(os.path.join(os.getcwd(), 'schemas', output_schema + '.json')) as f:
            out_schema = json.load(f)

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            if in_schema is not None:
                data = request.get_json(force=False)

                if data is None:
                    return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200

                try:
                    validate(data, in_schema)
                except ValidationError:
                    return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200

            output = func(*args, **kwargs)

            if out_schema is not None:
                response = output[0] if isinstance(output, tuple) else output
                if response is None or 'get_data' not in response:
                    raise DebuggableException('Response is probably not a response object')

                out_data = response.get_data()

                try:
                    validate(json.loads(out_data), out_schema)
                except ValidationError as e:
                    raise DebuggableException('Schema validation failed') from e

            return output

        return decorated_func

    return decorator
