import os
import subprocess
import sys

from primitive_db.constants import META_FILE
from primitive_db.utils import load_metadata, load_table_data
from tests.support import DatabaseTestCase


class CliTests(DatabaseTestCase):
    def run_session(self, commands):
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONUTF8"] = "1"

        result = subprocess.run(
            [sys.executable, "-m", "primitive_db.main"],
            input="\n".join(commands) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            timeout=30,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stdout

    def test_full_cli_scenario(self):
        output = self.run_session(
            [
                "create_table users name:str age:int is_active:bool",
                'insert into users values ("Sergei", 28, true)',
                "select from users where age=28",
                'update users set age=29 where name="Sergei"',
                "select from users where age=29",
                "delete from users where ID=1",
                "n",
                "info users",
                "delete from users where ID=1",
                "y",
                "info users",
                "drop_table users",
                "y",
                "list_tables",
                "exit",
            ]
        )

        self.assertIn('Таблица "users" успешно создана', output)
        self.assertIn("Sergei", output)
        self.assertIn("успешно обновлена", output)
        self.assertIn("Операция отменена.", output)
        self.assertIn("Количество записей: 1", output)
        self.assertIn("Количество записей: 0", output)
        self.assertIn("Функция insert выполнилась", output)
        self.assertIn("Функция select выполнилась", output)
        self.assertIn('Таблица "users" успешно удалена.', output)
        self.assertEqual(load_metadata(META_FILE), {})

    def test_persistence_between_processes(self):
        self.run_session(
            [
                "create_table users name:str age:int",
                'insert into users values ("Persisted user", 42)',
                "exit",
            ]
        )

        output = self.run_session(
            [
                "list_tables",
                "select from users",
                "info users",
                "exit",
            ]
        )

        self.assertIn("- users", output)
        self.assertIn("Persisted user", output)
        self.assertIn("Количество записей: 1", output)
        self.assertEqual(load_table_data("users")[0]["age"], 42)

    def test_invalid_commands_do_not_terminate_session(self):
        output = self.run_session(
            [
                "unknown",
                "create_table users age:int",
                "insert into users values (true)",
                "insert into users values (28)",
                "select from users where missing=1",
                "info users",
                "exit",
            ]
        )

        self.assertIn("Функции unknown нет.", output)
        self.assertIn("ожидает int", output)
        self.assertIn("Количество записей: 1", output)
        self.assertEqual(load_table_data("users")[0]["age"], 28)

    def test_eof_during_confirmation_does_not_delete_table(self):
        output = self.run_session(
            [
                "create_table users name:str",
                "drop_table users",
            ]
        )

        self.assertIn("До свидания!", output)
        self.assertIn("users", load_metadata(META_FILE))
