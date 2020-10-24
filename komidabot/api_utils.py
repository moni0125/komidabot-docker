import json
import os
import sys
import traceback
from functools import wraps

from flask import jsonify, request
from jsonschema import ValidationError, Draft7Validator, RefResolver
from werkzeug.http import HTTP_STATUS_CODES

from komidabot.app import get_app
from komidabot.debug.state import DebuggableException

__all__ = ['expects_schema', 'wrap_exceptions']


def response_ok():
    return jsonify({'status': 200, 'message': HTTP_STATUS_CODES[200]}), 200


def response_bad_request():
    return jsonify({'status': 400, 'message': HTTP_STATUS_CODES[400]}), 200


def response_unauthorized():
    return jsonify({'status': 401, 'message': HTTP_STATUS_CODES[401]}), 200


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
        input_schema = os.path.join(os.getcwd(), 'schemas', input_schema + '.json')
        with open(input_schema) as f:
            in_schema = json.load(f)

        Draft7Validator.check_schema(in_schema)
        in_resolver = RefResolver(base_uri='file:{}'.format(input_schema), referrer=in_schema)
        in_validator = Draft7Validator(in_schema, resolver=in_resolver)

    out_schema = None
    if output_schema is not None:
        output_schema = os.path.join(os.getcwd(), 'schemas', output_schema + '.json')
        with open(output_schema) as f:
            out_schema = json.load(f)

        Draft7Validator.check_schema(out_schema)
        out_resolver = RefResolver(base_uri='file:{}'.format(output_schema), referrer=out_schema)
        out_validator = Draft7Validator(out_schema, resolver=out_resolver)

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            if in_schema is not None:
                data = request.get_json(force=False)

                if data is None:
                    return response_bad_request()

                try:
                    in_validator.validate(data)
                except ValidationError:
                    return response_bad_request()

            output = func(*args, **kwargs)

            if out_schema is not None:
                response = output[0] if isinstance(output, tuple) else output
                if response is None or not callable(getattr(response, 'get_data', None)):
                    raise DebuggableException('Response is probably not a response object')

                out_data = response.get_data()

                try:
                    out_validator.validate(json.loads(out_data))
                except ValidationError as e:
                    raise DebuggableException('Schema validation failed') from e

            return output

        return decorated_func

    return decorator
