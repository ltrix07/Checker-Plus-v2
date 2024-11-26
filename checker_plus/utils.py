import json
from datetime import datetime, date
from typing import Dict, List, Any
from itertools import islice


def can_be_type(value: str, target_type) -> bool:
    try:
        target_type(value)
        return True
    except ValueError:
        return False


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


async def date_to_days(string_with_date: str) -> str:
    """
    Переводит дату, полученную с eBay в разницу дней начиная с сегодня.
    :param string_with_date: Строка даты с сайта.
    :return: Разницу дней.
    """
    if string_with_date:
        now_year = datetime.now().year
        date_ebay = datetime.strptime(string_with_date + ' ' + str(now_year), '%a, %b %d %Y').date()
        today = date.today()

        days_left = (date_ebay - today).days
        if days_left < 0:
            date_ebay = datetime.strptime(string_with_date + ' ' + str(now_year + 1), '%a, %b %d %Y').date()
            days_left = (date_ebay - today).days
            return str(days_left) + "days"
        else:
            return str(days_left) + "days"
    else:
        return "0days"


def get_next_batch(data: List[Dict[str, Any]], batch_size: int) -> List[Dict[str, Any]]:
    batch = data[:batch_size]
    del data[:batch_size]
    return batch


def logger_message_create(line_i: int, elem: str, type_: str):
    return f"In the line {line_i + 1} string '{elem}' cannot be cast to type {type_}." \
           f"Therefore, if data from the site is received incorrectly," \
           f"the quantity of goods will be 0."


def retype(value: Any, type_: type, def_value):
    try:
        return type_(value)
    except TypeError:
        return def_value
