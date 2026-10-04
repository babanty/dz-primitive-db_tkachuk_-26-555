import json
import os

from primitive_db.constants import META_FILE
from primitive_db.engine import run_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
    table_filepath,
)
from tests.support import DatabaseTestCase


class StorageTests(DatabaseTestCase):
    def test_unicode_round_trip(self):
        rows = [{"ID": 1, "name": "Иван Петров"}]
        save_table_data("users", rows)

        self.assertEqual(load_table_data("users"), rows)
        self.assertFalse(os.path.exists(table_filepath("users") + ".tmp"))

    def test_metadata_temporary_file_is_removed(self):
        save_metadata(META_FILE, {"users": {"ID": "int"}})

        self.assertFalse(os.path.exists(META_FILE + ".tmp"))
        self.assertIn("users", load_metadata(META_FILE))

    def test_path_traversal_is_rejected(self):
        for name in ("../users", "..\\users", "/users", "users/name", ""):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    table_filepath(name)

    def test_invalid_json_shape_is_rejected(self):
        with open(META_FILE, "w", encoding="utf-8") as destination:
            json.dump([], destination)

        with self.assertRaises(ValueError):
            load_metadata(META_FILE)

        save_table_data("users", {"not": "a list"})

        with self.assertRaises(ValueError):
            load_table_data("users")

    def test_corrupt_rows_do_not_get_overwritten(self):
        run_command("create_table users age:int")
        corrupt_rows = [{"ID": 1, "age": "not an integer"}]
        save_table_data("users", corrupt_rows)

        run_command("insert into users values (28)")

        self.assertEqual(load_table_data("users"), corrupt_rows)
        self.assertIn("ожидает int", self.output.getvalue())

    def test_recreated_table_has_no_old_records(self):
        run_command("create_table users name:str")
        run_command('insert into users values ("Old record")')
        run_command("drop_table users")

        run_command("create_table users age:int")
        run_command("insert into users values (28)")

        self.assertEqual(load_table_data("users"), [{"ID": 1, "age": 28}])

    def test_duplicate_creation_preserves_existing_records(self):
        run_command("create_table users name:str")
        run_command('insert into users values ("Existing record")')
        before = load_table_data("users")

        run_command("create_table users age:int")

        self.assertEqual(load_table_data("users"), before)
