from unittest.mock import Mock, patch

from primitive_db import core
from primitive_db.constants import CACHE_LIMIT, META_FILE
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.engine import run_command
from primitive_db.utils import load_metadata, load_table_data
from tests.support import DatabaseTestCase


class DecoratorTests(DatabaseTestCase):
    def test_expected_errors_are_handled(self):
        errors = (
            FileNotFoundError("missing"),
            KeyError("missing"),
            ValueError("invalid"),
            PermissionError("denied"),
        )

        for error in errors:
            with self.subTest(error=type(error).__name__):

                @handle_db_errors
                def operation():
                    """Raise the current expected error."""
                    raise error

                self.assertIsNone(operation())

        self.assertIn("Ошибка", self.output.getvalue())

    def test_error_decorator_preserves_return_value_and_name(self):
        @handle_db_errors
        def operation():
            """Return a normal result."""
            return 42

        self.assertEqual(operation(), 42)
        self.assertEqual(operation.__name__, "operation")
        self.assertEqual(operation.__doc__, "Return a normal result.")

    def test_confirmation_cancels_without_calling_operation(self):
        calls = []

        @confirm_action("тест")
        def operation():
            """Track execution."""
            calls.append(True)
            return 42

        with patch("builtins.input", return_value="n"):
            self.assertIsNone(operation())

        self.assertEqual(calls, [])

        with patch("builtins.input", return_value="y"):
            self.assertEqual(operation(), 42)

        self.assertEqual(calls, [True])

    def test_timing_uses_monotonic_clock(self):
        @log_time
        def operation():
            """Return a test result."""
            return 42

        with patch(
            "primitive_db.decorators.time.monotonic",
            side_effect=[10.0, 10.125],
        ):
            self.assertEqual(operation(), 42)

        self.assertIn(
            "Функция operation выполнилась за 0.125 секунд.",
            self.output.getvalue(),
        )

    def test_cache_computes_each_key_once(self):
        cache = create_cacher()
        factory = Mock(return_value={"value": 42})

        first = cache("key", factory)
        second = cache("key", factory)

        self.assertEqual(first, {"value": 42})
        self.assertIs(first, second)
        factory.assert_called_once_with()

    def test_cache_instances_are_independent(self):
        first_cache = create_cacher()
        second_cache = create_cacher()

        self.assertEqual(first_cache("key", lambda: 1), 1)
        self.assertEqual(second_cache("key", lambda: 2), 2)

    def test_cache_does_not_store_failed_computations(self):
        cache = create_cacher()
        factory = Mock(side_effect=[ValueError("failure"), 42])

        with self.assertRaises(ValueError):
            cache("key", factory)

        self.assertEqual(cache("key", factory), 42)
        self.assertEqual(factory.call_count, 2)

    def test_cache_is_bounded(self):
        cache = create_cacher()

        for key in range(CACHE_LIMIT + 1):
            cache(key, lambda key=key: key)

        factory = Mock(return_value="recomputed")
        self.assertEqual(cache(0, factory), "recomputed")
        factory.assert_called_once_with()

    def test_select_cache_is_used_and_results_are_independent(self):
        rows = [{"ID": 1, "name": "Cache test"}]

        with patch("primitive_db.core._select_cache", create_cacher()):
            with patch(
                "primitive_db.core.matches",
                wraps=core.matches,
            ) as matches:
                first = core.select(rows)
                first[0]["name"] = "Modified externally"
                second = core.select(rows)

        self.assertEqual(second[0]["name"], "Cache test")
        self.assertEqual(matches.call_count, 1)

    def test_select_cache_changes_when_data_changes(self):
        rows = [{"ID": 1, "age": 28}]

        with patch("primitive_db.core._select_cache", create_cacher()):
            self.assertEqual(core.select(rows, {"age": 28}), rows)

            rows[0]["age"] = 29
            self.assertEqual(core.select(rows, {"age": 28}), [])
            self.assertEqual(core.select(rows, {"age": 29}), rows)

            rows.append({"ID": 2, "age": 30})
            self.assertEqual(len(core.select(rows)), 2)

            rows.clear()
            self.assertEqual(core.select(rows), [])

    def test_cancelled_delete_preserves_persisted_rows(self):
        run_command("create_table users name:str")
        run_command('insert into users values ("Sergei")')
        before = load_table_data("users")

        with patch("builtins.input", return_value="n"):
            run_command("delete from users where ID=1")

        self.assertEqual(load_table_data("users"), before)
        self.assertIn("Операция отменена.", self.output.getvalue())

    def test_cancelled_drop_preserves_table(self):
        run_command("create_table users name:str")
        run_command('insert into users values ("Sergei")')

        with patch("builtins.input", return_value="n"):
            run_command("drop_table users")

        self.assertIn("users", load_metadata(META_FILE))
        self.assertEqual(len(load_table_data("users")), 1)

    def test_core_errors_return_none(self):
        self.assertIsNone(core.insert({}, "missing", []))
        self.assertIsNone(core.create_table({}, "users", ["age:float"]))
