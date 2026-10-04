"""Command parsing."""

import shlex


def parse_command(user_input):
    """Parse table management commands into a command dictionary."""
    tokens = shlex.split(user_input)

    if not tokens:
        raise ValueError("Введите команду.")

    command = tokens[0].lower()

    if command in {"help", "exit", "list_tables"}:
        if len(tokens) != 1:
            raise ValueError(f"Команда {command} не принимает аргументы.")
        return {"command": command}

    if command == "create_table":
        if len(tokens) < 3:
            raise ValueError("Формат: create_table <таблица> <столбец:тип> ...")
        return {
            "command": command,
            "table_name": tokens[1],
            "columns": tokens[2:],
        }

    if command == "drop_table":
        if len(tokens) != 2:
            raise ValueError("Формат: drop_table <таблица>")
        return {"command": command, "table_name": tokens[1]}

    raise ValueError(f"Функции {tokens[0]} нет. Попробуйте снова.")
