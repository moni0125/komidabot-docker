import traceback
from functools import wraps


def check_exceptions(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print('Exception raised while calling {}: {}'.format(func.__name__, e))
            traceback.print_tb(e.__traceback__)

    return decorated_func
