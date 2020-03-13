from sys import stderr
from datetime import datetime, timezone
from json import dump, dumps, load, loads
from functools import wraps
from traceback import format_exc

# Output to stderr instead of stdout
def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

# Get the current time as either a timestamp or datetime object
def now(ts=False):
    utc = datetime.now(timezone.utc)
    return utc.timestamp() if ts else utc

# JSON encoder, converts a python object to a string
def jots(data, readable=False, dest=None):
    kwargs = dict()

    # If readable is set, it pretty prints the JSON to be more human-readable
    if readable:
        # kwargs["sort_keys"] = True
        kwargs["indent"] = 4 
        kwargs["separators"] = (",", ":")

    try:
        if dest:
            return dump(data, dest, ensure_ascii=False, **kwargs)

        return dumps(data, ensure_ascii=False, **kwargs)

    except ValueError as e:
        return None

# JSON decoder, converts a string to a python object
def jsto(data=None):
    try:
        # If not a string, treat like a file pointer
        if isinstance(data, str):
            dest = data
            return load(dest)

        return loads(data)

    except ValueError as e:
        eprint(e)
        return None  

# Automatically advances coroutine to accept sends
def coroutine(func):
    @wraps(func)
    def wrapper_coroutine(*args, **kwargs):
        coro = func(*args, **kwargs)
        coro.__next__()
        return coro

    return wrapper_coroutine

# Automatically implements loop and handles the exit exception
def generator(func):
    @wraps(func)
    @coroutine
    def wrapper_generator(*args, **kwargs):
        try:
            while True:
                yield from func(*args, **kwargs)

        except GeneratorExit:
            pass

    return wrapper_generator

# Syntactic sugar for a try/catch as a decorator using callback for exception
def trap(callback):
    def decorator_trap(func):
        @wraps(func)
        def wrapper_trap(*args, **kwargs):
            try:
                value = func(*args, **kwargs)

            except Exception as e:
                value = None
                callback(format_exc())
                
            return value

        return wrapper_trap

    return decorator_trap
