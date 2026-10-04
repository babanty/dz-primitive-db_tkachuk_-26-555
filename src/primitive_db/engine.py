"""Interactive command loop and command dispatch."""

import prompt

from primitive_db import core
from primitive_db.constants import HELP_TEXT, INPUT_PROMPT, META_FILE
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
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


def execute(user_input):
    """Execute one parsed command."""
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

    table_name = request["table_name"]

    if command == "create_table":
        result = core.create_table(metadata, table_name, request["columns"])
        if result is not None:
            save_table_data(table_name, [])
            save_metadata(META_FILE, result)
            columns = format_schema(result[table_name])
            print(f'Таблица "{table_name}" успешно создана со столбцами: {columns}')

    elif command == "drop_table":
        result = core.drop_table(metadata, table_name)
        if result is not None:
            remove_table_data(table_name)
            save_metadata(META_FILE, result)
            print(f'Таблица "{table_name}" успешно удалена.')

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
