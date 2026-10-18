from contextlib import contextmanager
from time import perf_counter


@contextmanager
def profile():
    result = {}
    start = perf_counter()
    try:
        yield result
    finally:
        result['seconds'] = perf_counter() - start
