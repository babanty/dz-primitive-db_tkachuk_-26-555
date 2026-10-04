from primitive_db import core
from primitive_db.constants import META_FILE
from primitive_db.engine import run_command
from primitive_db.utils import load_metadata, load_table_data
from tests.support import DatabaseTestCase


class CrudTests(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        run_command("create_table users name:str age:int is_active:bool")

    def add_user(self, name="Sergei", age=28, active="true"):
        run_command(f'insert into users values ("{name}", {age}, {active})')

    def test_full_crud_cycle(self):
        self.add_user()

        rows = load_table_data("users")
        self.assertEqual(
            rows,
            [{"ID": 1, "name": "Sergei", "age": 28, "is_active": True}],
        )

        run_command("select from users where age=28")
        self.assertIn("Sergei", self.output.getvalue())

        run_command('update users set age=29, is_active=false where name="Sergei"')

        rows = load_table_data("users")
        self.assertEqual(rows[0]["age"], 29)
        self.assertIs(rows[0]["is_active"], False)

        run_command("delete from users where ID=1")
        self.assertEqual(load_table_data("users"), [])

        run_command("info users")
        self.assertIn("Количество записей: 0", self.output.getvalue())

    def test_wrong_types_and_arity_do_not_insert(self):
        for command in (
            'insert into users values ("Sergei", true, true)',
            'insert into users values ("Sergei", "28", true)',
            'insert into users values ("Sergei", 28, 1)',
            'insert into users values ("Sergei", 28)',
            'insert into users values (1, "Sergei", 28, true)',
        ):
            run_command(command)

        self.assertEqual(load_table_data("users"), [])

    def test_invalid_update_does_not_change_data(self):
        self.add_user()
        before = load_table_data("users")

        for command in (
            "update users set ID=99 where ID=1",
            'update users set age="29" where ID=1',
            "update users set unknown=29 where ID=1",
            "update users set age=29 where missing=1",
            'update users set age=29 where ID="1"',
        ):
            run_command(command)
            self.assertEqual(load_table_data("users"), before)

    def test_id_generation_after_deleting_middle_record(self):
        self.add_user("First")
        self.add_user("Second")
        self.add_user("Third")

        run_command("delete from users where ID=2")
        self.add_user("Fourth")

        identifiers = [row["ID"] for row in load_table_data("users")]
        self.assertEqual(identifiers, [1, 3, 4])

    def test_update_and_delete_only_matching_records(self):
        self.add_user("First", age=20)
        self.add_user("Second", age=30)
        self.add_user("Third", age=20)

        run_command("update users set is_active=false where age=20")

        rows = load_table_data("users")
        self.assertEqual(
            [row["is_active"] for row in rows],
            [False, True, False],
        )

        run_command("delete from users where is_active=false")

        rows = load_table_data("users")
        self.assertEqual([row["name"] for row in rows], ["Second"])

    def test_select_returns_independent_rows(self):
        self.add_user()
        rows = load_table_data("users")

        selected = core.select(rows)
        selected[0]["name"] = "Changed"

        self.assertEqual(rows[0]["name"], "Sergei")

    def test_boolean_is_not_integer_in_conditions(self):
        self.assertEqual(core.select([{"value": True}], {"value": 1}), [])

    def test_insert_returns_rows_without_persisting_them(self):
        metadata = load_metadata(META_FILE)
        rows = core.insert(metadata, "users", ["Sergei", 28, True])

        self.assertEqual(rows[0]["ID"], 1)
        self.assertEqual(load_table_data("users"), [])

    def test_no_matches_leave_data_unchanged(self):
        self.add_user()
        before = load_table_data("users")

        run_command("update users set age=29 where ID=999")
        run_command("delete from users where ID=999")

        self.assertEqual(load_table_data("users"), before)
        self.assertIn("Подходящих записей нет.", self.output.getvalue())

    def test_empty_table_still_validates_conditions(self):
        run_command("select from users where missing=1")
        run_command('update users set age="bad" where ID=1')

        self.assertIn("не существует", self.output.getvalue())
        self.assertIn("ожидает int", self.output.getvalue())
