"""Interactive command loop and command dispatch."""

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import HELP_TEXT, ID_COLUMN, INPUT_PROMPT, META_FILE
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Print supported commands."""
    print(HELP_TEXT)


def format_schema(schema):
    """Format a schema for console output."""
    return ", ".join(f"{name}:{type_name}" for name, type_name in schema.items())


def print_rows(schema, rows):
    """Render rows in schema order using PrettyTable."""
    table = PrettyTable()
    table.field_names = list(schema)

    for row in rows:
        table.add_row([row[column] for column in schema])

    print(table)


def execute_table_command(metadata, request):
    """Execute a table creation or removal command."""
    table_name = request["table_name"]

    if request["command"] == "create_table":
        result = core.create_table(metadata, table_name, request["columns"])

        if result is not None:
            save_table_data(table_name, [])
            save_metadata(META_FILE, result)
            columns = format_schema(result[table_name])
            print(f'Таблица "{table_name}" успешно создана со столбцами: {columns}')

    else:
        result = core.drop_table(metadata, table_name)

        if result is not None:
            remove_table_data(table_name)
            save_metadata(META_FILE, result)
            print(f'Таблица "{table_name}" успешно удалена.')


def report_changes(command, table_name, identifiers):
    """Print update or deletion results after persistence succeeds."""
    if not identifiers:
        print("Подходящих записей нет.")
        return

    for identifier in identifiers:
        if command == "update":
            print(
                f'Запись с ID={identifier} в таблице "{table_name}" успешно обновлена.'
            )
        else:
            print(
                f'Запись с ID={identifier} успешно удалена из таблицы "{table_name}".'
            )


def execute_data_command(metadata, request):
    """Validate and execute a CRUD or info request."""
    command = request["command"]
    table_name = request["table_name"]
    schema = core.require_table(metadata, table_name)

    if command == "insert":
        result = core.insert(metadata, table_name, request["values"])

        if result is not None:
            save_table_data(table_name, result)
            identifier = result[-1][ID_COLUMN]
            print(
                f'Запись с ID={identifier} успешно добавлена в таблицу "{table_name}".'
            )
        return

    rows = load_table_data(table_name)
    core.validate_rows(schema, rows)

    if command == "info":
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {format_schema(schema)}")
        print(f"Количество записей: {len(rows)}")
        return

    where_clause = request["where_clause"]

    if where_clause is not None:
        core.validate_fields(schema, where_clause)

    if command == "select":
        result = core.select(rows, where_clause)
        if result is not None:
            print_rows(schema, result)
        return

    identifiers = [row[ID_COLUMN] for row in rows if core.matches(row, where_clause)]

    if command == "update":
        set_clause = request["set_clause"]
        core.validate_fields(schema, set_clause, allow_id=False)
        result = core.update(rows, set_clause, where_clause)
    else:
        result = core.delete(rows, where_clause)

    if result is not None:
        save_table_data(table_name, result)
        report_changes(command, table_name, identifiers)


def execute(user_input):
    """Execute one parsed command and return False only for exit."""
    request = parse_command(user_input)
    command = request["command"]

    if command == "exit":
        return False

    if command == "help":
        print_help()
        return True

    metadata = load_metadata(META_FILE)

    if command == "list_tables":
        if not metadata:
            print("Таблиц пока нет.")
        for table_name in sorted(metadata):
            print(f"- {table_name}")
        return True

    if command in {"create_table", "drop_table"}:
        execute_table_command(metadata, request)
    else:
        execute_data_command(metadata, request)

    return True


def run_command(user_input):
    """Execute a command without terminating the session on user errors."""
    try:
        return execute(user_input)
    except KeyError as error:
        print(f"Ошибка: {error.args[0]}")
    except ValueError as error:
        print(f"Ошибка валидации: {error}")
    except OSError as error:
        print(f"Ошибка файловой системы: {error}")
    return None


def run():
    """Run the interactive database session."""
    print_help()

    while True:
        try:
            user_input = prompt.string(INPUT_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break

        if run_command(user_input) is False:
            print("До свидания!")
            break
