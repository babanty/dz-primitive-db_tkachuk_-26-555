"""Parsing of commands, typed values and equality clauses."""

import json
import shlex


def tokenize_plain(fragment):
    """Tokenize unquoted command text using shlex."""
    if "'" in fragment:
        raise ValueError("Строковые значения заключайте в двойные кавычки.")

    lexer = shlex.shlex(fragment, posix=True, punctuation_chars="(),=")
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""

    tokens = []
    for token in lexer:
        if token and all(character in "(),=" for character in token):
            tokens.extend(token)
        else:
            tokens.append(token)
    return tokens


def tokenize(user_input):
    """Preserve JSON strings while tokenizing the surrounding command."""
    tokens = []
    position = 0
    decoder = json.JSONDecoder()

    while position < len(user_input):
        quote_position = user_input.find('"', position)

        if quote_position == -1:
            tokens.extend(tokenize_plain(user_input[position:]))
            break

        tokens.extend(tokenize_plain(user_input[position:quote_position]))

        try:
            value, consumed = decoder.raw_decode(user_input[quote_position:])
        except json.JSONDecodeError as error:
            raise ValueError("Некорректная строка в двойных кавычках.") from error

        if not isinstance(value, str):
            raise ValueError("Ожидалось строковое значение.")

        tokens.append(user_input[quote_position : quote_position + consumed])
        position = quote_position + consumed

    return tokens


def parse_value(token):
    """Parse a quoted string, integer or boolean literal."""
    if token.startswith('"'):
        value = json.loads(token)
        if isinstance(value, str):
            return value

    if token.lower() == "true":
        return True

    if token.lower() == "false":
        return False

    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits and digits.isascii() and digits.isdecimal():
        return int(token)

    raise ValueError(
        f"Некорректное значение: {token}. "
        "Ожидается int, bool или строка в двойных кавычках."
    )


def parse_values(tokens):
    """Parse a parenthesized comma-separated list of typed values."""
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Значения должны быть заключены в скобки.")

    inner = tokens[1:-1]
    if not inner:
        return []

    if len(inner) % 2 == 0 or any(token != "," for token in inner[1::2]):
        raise ValueError("Разделяйте значения запятыми.")

    return [parse_value(token) for token in inner[::2]]


def parse_where(tokens):
    """Parse one equality condition into a dictionary."""
    if len(tokens) != 3 or tokens[1] != "=":
        raise ValueError("Формат условия: <столбец> = <значение>.")

    return {tokens[0]: parse_value(tokens[2])}


def parse_set(tokens):
    """Parse comma-separated assignments into a dictionary."""
    if not tokens or (len(tokens) + 1) % 4 != 0:
        raise ValueError("Формат set: <столбец> = <значение>, ...")

    assignments = {}

    for position in range(0, len(tokens), 4):
        assignment = parse_where(tokens[position : position + 3])
        column = next(iter(assignment))

        if column in assignments:
            raise ValueError(f"Повторяющийся столбец: {column}.")

        assignments.update(assignment)

        separator_position = position + 3
        if separator_position < len(tokens) and tokens[separator_position] != ",":
            raise ValueError("Разделяйте присваивания запятыми.")

    return assignments


def parse_update(tokens):
    """Parse an update command with a mandatory where condition."""
    if len(tokens) < 10 or tokens[2].lower() != "set":
        raise ValueError(
            "Формат: update <таблица> set <столбец> = <значение> "
            "where <столбец> = <значение>."
        )

    assignments_and_condition = tokens[3:]
    where_position = None

    for position in range(3, len(assignments_and_condition), 4):
        if assignments_and_condition[position].lower() == "where":
            where_position = position
            break

    if where_position is None:
        raise ValueError("Для update обязательно условие where.")

    return {
        "command": "update",
        "table_name": tokens[1],
        "set_clause": parse_set(assignments_and_condition[:where_position]),
        "where_clause": parse_where(assignments_and_condition[where_position + 1 :]),
    }


def parse_command(user_input):
    """Parse a supported command into a structured request."""
    tokens = tokenize(user_input)

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

    if command in {"drop_table", "info"}:
        if len(tokens) != 2:
            raise ValueError(f"Формат: {command} <таблица>")
        return {"command": command, "table_name": tokens[1]}

    if command == "insert":
        if (
            len(tokens) < 6
            or tokens[1].lower() != "into"
            or tokens[3].lower() != "values"
        ):
            raise ValueError("Формат: insert into <таблица> values (...)")

        return {
            "command": command,
            "table_name": tokens[2],
            "values": parse_values(tokens[4:]),
        }

    if command in {"select", "delete"}:
        if len(tokens) < 3 or tokens[1].lower() != "from":
            raise ValueError(f"Формат: {command} from <таблица> [where ...]")

        where_clause = None

        if len(tokens) > 3:
            if tokens[3].lower() != "where":
                raise ValueError("Ожидалось условие where.")
            where_clause = parse_where(tokens[4:])

        if command == "delete" and where_clause is None:
            raise ValueError("Для delete обязательно условие where.")

        return {
            "command": command,
            "table_name": tokens[2],
            "where_clause": where_clause,
        }

    if command == "update":
        return parse_update(tokens)

    raise ValueError(f"Функции {tokens[0]} нет. Попробуйте снова.")
