"""JSON storage helpers."""

import json
import os

from primitive_db.constants import DATA_DIR, FILE_ENCODING


def validate_identifier(name):
    """Validate an ASCII table or column identifier."""
    if not isinstance(name, str) or not name.isascii() or not name.isidentifier():
        raise ValueError(f"Некорректное имя: {name}.")
    return name


def load_metadata(filepath):
    """Load a JSON object, returning an empty object for a missing file."""
    try:
        with open(filepath, encoding=FILE_ENCODING) as source:
            metadata = json.load(source)
    except FileNotFoundError:
        return {}

    if not isinstance(metadata, dict):
        raise ValueError("Файл метаданных должен содержать JSON-объект.")
    return metadata


def save_json(filepath, data):
    """Atomically replace an individual JSON file."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

    temporary_path = f"{filepath}.tmp"

    try:
        with open(temporary_path, "w", encoding=FILE_ENCODING) as destination:
            json.dump(data, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
        os.replace(temporary_path, filepath)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def save_metadata(filepath, data):
    """Save database metadata."""
    save_json(filepath, data)


def table_filepath(table_name):
    """Return a safe path for a table data file."""
    validate_identifier(table_name)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Load table rows, returning an empty list for a missing file."""
    filepath = table_filepath(table_name)

    try:
        with open(filepath, encoding=FILE_ENCODING) as source:
            rows = json.load(source)
    except FileNotFoundError:
        return []

    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Файл таблицы должен содержать список записей.")
    return rows


def save_table_data(table_name, data):
    """Save rows to the table data file."""
    save_json(table_filepath(table_name), data)


def remove_table_data(table_name):
    """Remove a table data file if it exists."""
    filepath = table_filepath(table_name)

    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
