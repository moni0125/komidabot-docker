import traceback
from functools import wraps
from typing import List, Tuple, TypeVar


def check_exceptions(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print('Exception raised while calling {}: {}'.format(func.__name__, e))
            traceback.print_tb(e.__traceback__)

    return decorated_func


T = TypeVar('T')


def get_list_diff(old_list: List[T], new_list: List[T]) -> Tuple[List[T], List[T], List[T]]:
    """
    Computes the difference between two lists.
    :param old_list: The old list.
    :param new_list: The new list.
    :return: A 3-tuple containing the following lists in order: items still present, items added, items removed
    """

    unchanged = [item for item in old_list if item in new_list]
    added = [item for item in new_list if item not in unchanged]
    removed = [item for item in old_list if item not in unchanged]

    assert len(unchanged) + len(removed) == len(old_list)
    assert len(unchanged) + len(added) == len(new_list)

    return unchanged, added, removed
