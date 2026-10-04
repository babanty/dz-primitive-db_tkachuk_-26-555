import os

from primitive_db import core
from primitive_db.constants import META_FILE
from primitive_db.engine import run_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    table_filepath,
)
from tests.support import DatabaseTestCase


class TableTests(DatabaseTestCase):
    def test_missing_metadata_is_empty(self):
        self.assertEqual(load_metadata(META_FILE), {})

    def test_metadata_round_trip(self):
        metadata = {"users": {"ID": "int", "name": "str"}}
        save_metadata(META_FILE, metadata)
        self.assertEqual(load_metadata(META_FILE), metadata)

    def test_create_adds_id_first(self):
        metadata = core.create_table({}, "users", ["name:str", "age:int"])
        self.assertEqual(list(metadata["users"]), ["ID", "name", "age"])

    def test_explicit_id_is_not_duplicated(self):
        metadata = core.create_table({}, "users", ["name:str", "ID:int"])
        self.assertEqual(list(metadata["users"]), ["ID", "name"])

    def test_invalid_columns(self):
        for columns in (
            ["age:float"],
            ["name:str", "name:int"],
            ["ID:str"],
            ["bad-column:str"],
            ["name"],
        ):
            with self.subTest(columns=columns):
                with self.assertRaises(ValueError):
                    core.validate_columns(columns)

    def test_create_list_and_drop(self):
        run_command("create_table users name:str")
        self.assertIn("users", load_metadata(META_FILE))
        self.assertEqual(load_table_data("users"), [])
        self.assertTrue(os.path.exists(table_filepath("users")))

        run_command("list_tables")
        self.assertIn("- users", self.output.getvalue())

        run_command("drop_table users")
        self.assertEqual(load_metadata(META_FILE), {})
        self.assertFalse(os.path.exists(table_filepath("users")))

    def test_duplicate_does_not_destroy_table(self):
        run_command("create_table users name:str")
        before = load_metadata(META_FILE)

        run_command("create_table users age:int")

        self.assertEqual(load_metadata(META_FILE), before)
        self.assertIn("уже существует", self.output.getvalue())

    def test_invalid_commands_do_not_modify_metadata(self):
        for command in (
            "create_table ../users name:str",
            "create_table users age:float",
            "drop_table missing",
            "unknown",
            "list_tables extra",
        ):
            run_command(command)

        self.assertEqual(load_metadata(META_FILE), {})
        self.assertIn("Ошибка", self.output.getvalue())

    def test_corrupt_metadata_is_not_overwritten(self):
        with open(META_FILE, "w", encoding="utf-8") as destination:
            destination.write("{broken")

        run_command("create_table users name:str")

        with open(META_FILE, encoding="utf-8") as source:
            self.assertEqual(source.read(), "{broken")
