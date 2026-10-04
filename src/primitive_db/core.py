"""Table management and database business logic."""

from primitive_db.constants import FIRST_ID, ID_COLUMN, ID_TYPE, VALID_TYPES
from primitive_db.utils import load_table_data, validate_identifier


def require_table(metadata, table_name):
    """Return a table schema or report a missing table."""
    validate_identifier(table_name)

    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    if not isinstance(schema, dict) or schema.get(ID_COLUMN) != ID_TYPE:
        raise ValueError(f'Некорректная схема таблицы "{table_name}".')

    for column, type_name in schema.items():
        validate_identifier(column)
        if not isinstance(type_name, str) or type_name not in VALID_TYPES:
            raise ValueError(f'Некорректные типы таблицы "{table_name}".')

    return schema


def validate_columns(columns):
    """Validate column declarations and prepend the generated ID column."""
    if not columns:
        raise ValueError("Укажите хотя бы один столбец.")

    schema = {ID_COLUMN: ID_TYPE}
    declared_names = set()

    for column in columns:
        if column.count(":") != 1:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")

        name, type_name = column.split(":")
        validate_identifier(name)

        if type_name not in VALID_TYPES:
            raise ValueError(f"Неподдерживаемый тип: {type_name}.")

        if name in declared_names:
            raise ValueError(f"Повторяющийся столбец: {name}.")
        declared_names.add(name)

        if name.lower() == ID_COLUMN.lower():
            if name != ID_COLUMN or type_name != ID_TYPE:
                raise ValueError("Системный столбец должен называться ID:int.")
            continue

        schema[name] = type_name

    return schema


def validate_fields(schema, fields, allow_id=True):
    """Validate field names and exact Python types against a schema."""
    for column, value in fields.items():
        if column not in schema:
            raise KeyError(f'Столбец "{column}" не существует.')

        if column == ID_COLUMN and not allow_id:
            raise ValueError("Изменять ID запрещено.")

        expected_type = VALID_TYPES[schema[column]]

        if type(value) is not expected_type:
            raise ValueError(
                f'Столбец "{column}" ожидает {schema[column]}, получено: {value!r}.'
            )


def validate_rows(schema, rows):
    """Check persisted rows for schema consistency and unique IDs."""
    identifiers = set()

    for row in rows:
        if set(row) != set(schema):
            raise ValueError("Структура записи не соответствует схеме таблицы.")

        validate_fields(schema, row)
        identifier = row[ID_COLUMN]

        if identifier < FIRST_ID or identifier in identifiers:
            raise ValueError("Файл таблицы содержит некорректные или повторные ID.")

        identifiers.add(identifier)


def create_table(metadata, table_name, columns):
    """Add a validated table schema to metadata."""
    validate_identifier(table_name)

    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    schema = validate_columns(columns)
    metadata[table_name] = schema
    return metadata


def drop_table(metadata, table_name):
    """Remove an existing table schema."""
    require_table(metadata, table_name)
    del metadata[table_name]
    return metadata


def matches(row, where_clause):
    """Check equality conditions without treating bool as int."""
    if where_clause is None:
        return True

    return all(
        column in row and type(row[column]) is type(value) and row[column] == value
        for column, value in where_clause.items()
    )


def insert(metadata, table_name, values):
    """Validate values, generate an ID and return rows with the new record."""
    schema = require_table(metadata, table_name)
    columns = [column for column in schema if column != ID_COLUMN]

    if len(values) != len(columns):
        raise ValueError(
            f"Ожидалось значений: {len(columns)}, получено: {len(values)}."
        )

    fields = dict(zip(columns, values, strict=True))
    validate_fields(schema, fields, allow_id=False)

    rows = load_table_data(table_name)
    validate_rows(schema, rows)

    identifier = (
        max(
            (row[ID_COLUMN] for row in rows),
            default=FIRST_ID - 1,
        )
        + 1
    )

    rows.append({ID_COLUMN: identifier, **fields})
    return rows


def select(table_data, where_clause=None):
    """Return independent copies of rows matching the optional condition."""
    return [row.copy() for row in table_data if matches(row, where_clause)]


def update(table_data, set_clause, where_clause):
    """Return rows with matching records updated, preserving input rows."""
    if ID_COLUMN in set_clause:
        raise ValueError("Изменять ID запрещено.")

    result = []

    for row in table_data:
        updated_row = row.copy()

        if matches(row, where_clause):
            for column, value in set_clause.items():
                if column not in row:
                    raise KeyError(f'Столбец "{column}" не существует.')
                if type(value) is not type(row[column]):
                    raise ValueError(f'Неверный тип столбца "{column}".')

            updated_row.update(set_clause)

        result.append(updated_row)

    return result


def delete(table_data, where_clause):
    """Return rows that do not match a mandatory deletion condition."""
    if not where_clause:
        raise ValueError("Для удаления обязательно непустое условие.")

    return [row.copy() for row in table_data if not matches(row, where_clause)]
