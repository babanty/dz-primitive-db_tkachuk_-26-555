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
  info <таблица> - информация о таблице

Операции с данными:
  insert into <таблица> values (<значение>, ...)
  select from <таблица>
  select from <таблица> where <столбец> = <значение>
  update <таблица> set <столбец> = <значение> where <столбец> = <значение>
  delete from <таблица> where <столбец> = <значение>

В update можно указать несколько присваиваний через запятую.

Общие команды:
  help - справочная информация
  exit - выход

Типы: int, str, bool. Все поля обязательны.
Строки пишутся в двойных кавычках. Логические значения: true и false.
ID:int добавляется автоматически и недоступен для изменения.
"""
