"""Error handling, confirmations, timing and closure-based caching."""

import time

from primitive_db.constants import CACHE_LIMIT, CONFIRM_RESPONSE


def preserve_metadata(wrapper, original):
    """Preserve basic function metadata without additional dependencies."""
    wrapper.__name__ = original.__name__
    wrapper.__doc__ = original.__doc__
    wrapper.__module__ = original.__module__
    wrapper.__wrapped__ = original
    return wrapper


def handle_db_errors(function):
    """Print expected database errors and return None on failure."""

    def wrapper(*args, **kwargs):
        """Run the wrapped function with centralized error handling."""
        try:
            return function(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: {error.args[0]}")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка файловой системы: {error}")
        return None

    return preserve_metadata(wrapper, function)


def confirm_action(action_name):
    """Create a decorator that requires confirmation before execution."""

    def decorator(function):
        """Wrap a potentially destructive operation."""

        def wrapper(*args, **kwargs):
            """Ask for confirmation and cancel unless the answer is y."""
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip().lower() != CONFIRM_RESPONSE:
                print("Операция отменена.")
                return None

            return function(*args, **kwargs)

        return preserve_metadata(wrapper, function)

    return decorator


def log_time(function):
    """Print elapsed monotonic time, including failed executions."""

    def wrapper(*args, **kwargs):
        """Measure the wrapped operation."""
        started_at = time.monotonic()

        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд.")

    return preserve_metadata(wrapper, function)


def create_cacher():
    """Create an independent bounded cache stored in a closure."""
    cache = {}

    def cache_result(key, value_func):
        """Return a cached result or compute and remember it."""
        if key not in cache:
            value = value_func()

            if len(cache) >= CACHE_LIMIT:
                oldest_key = next(iter(cache))
                del cache[oldest_key]

            cache[key] = value

        return cache[key]

    return cache_result
