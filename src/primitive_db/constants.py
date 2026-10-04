"""Shared application constants."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
FILE_ENCODING = "utf-8"

ID_COLUMN = "ID"
ID_TYPE = "int"
FIRST_ID = 1

VALID_TYPES = {
    "int": int,
    "str": str,
    "bool": bool,
}

CACHE_LIMIT = 128
CONFIRM_RESPONSE = "y"
INPUT_PROMPT = "Введите команду: "

HELP_TEXT = """
***База данных***

Управление таблицами:
  create_table <таблица> <столбец:тип> ... - создать таблицу
  list_tables - показать таблицы
  drop_table <таблица> - удалить таблицу

Общие команды:
  help - справочная информация
  exit - выход

Типы столбцов: int, str, bool.
Столбец ID:int добавляется автоматически.
"""
