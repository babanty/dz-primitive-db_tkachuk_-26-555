"""Table management and database business logic."""

from primitive_db.constants import ID_COLUMN, ID_TYPE, VALID_TYPES
from primitive_db.utils import validate_identifier


def require_table(metadata, table_name):
    """Return a table schema or report a missing table."""
    validate_identifier(table_name)

    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    if not isinstance(schema, dict) or schema.get(ID_COLUMN) != ID_TYPE:
        raise ValueError(f'Некорректная схема таблицы "{table_name}".')

    if any(type_name not in VALID_TYPES for type_name in schema.values()):
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
