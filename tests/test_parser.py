import unittest

from primitive_db.parser import parse_command, parse_value


class ParserTests(unittest.TestCase):
    def test_typed_values(self):
        self.assertEqual(parse_value("28"), 28)
        self.assertEqual(parse_value("-28"), -28)
        self.assertIs(parse_value("true"), True)
        self.assertIs(parse_value("false"), False)
        self.assertEqual(parse_value('"28"'), "28")
        self.assertEqual(parse_value('"true"'), "true")

    def test_insert_with_punctuation_inside_string(self):
        request = parse_command(
            'insert into users values ("Иван, Петров = active", 28, true)'
        )

        self.assertEqual(
            request["values"],
            ["Иван, Петров = active", 28, True],
        )

    def test_escaped_string(self):
        request = parse_command(
            r'insert into users values ("He said \"hello\"", 28, true)'
        )

        self.assertEqual(request["values"][0], 'He said "hello"')

    def test_apostrophe_inside_double_quotes(self):
        request = parse_command("""insert into users values ("O'Brien", 28, true)""")

        self.assertEqual(request["values"][0], "O'Brien")

    def test_select_condition(self):
        request = parse_command('select from users where name="Иван Петров"')

        self.assertEqual(request["where_clause"], {"name": "Иван Петров"})

    def test_update_multiple_fields(self):
        request = parse_command(
            'update users set age=29, name="where, set = value" where ID=1'
        )

        self.assertEqual(
            request["set_clause"],
            {"age": 29, "name": "where, set = value"},
        )
        self.assertEqual(request["where_clause"], {"ID": 1})

    def test_keywords_are_case_insensitive(self):
        request = parse_command("SELECT FROM users WHERE age=28")

        self.assertEqual(request["command"], "select")
        self.assertEqual(request["where_clause"], {"age": 28})

    def test_invalid_commands(self):
        commands = (
            "",
            "unknown",
            "select users",
            "select from users unexpected",
            "delete from users",
            "update users set age=29",
            "update users set age=29, age=30 where ID=1",
            "insert into users values (name, 28, true)",
            'insert into users values ("name", 28, true,)',
            'insert into users values ("unterminated, 28, true)',
            'insert into users values ("name" "surname", 28, true)',
            "select from users where age=28 extra",
            "exit extra",
        )

        for command in commands:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    parse_command(command)
