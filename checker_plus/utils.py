import json
from datetime import datetime, date
from typing import Dict, List, Any, Literal


def can_be_type(value: str, target_type) -> bool:
    try:
        target_type(value)
        return True
    except ValueError:
        return False


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


async def date_to_days(string_with_date: str) -> str:
    """
    Переводит дату, полученную с eBay, в разницу дней начиная с сегодня.
    :param string_with_date: Строка даты с сайта.
    :return: Разница дней.
    """
    if string_with_date:
        today = date.today()
        current_year = today.year

        try:
            date_ebay = datetime.strptime(string_with_date + f' {current_year}', '%a, %b %d %Y').date()
        except ValueError:
            return "Invalid date format"

        if date_ebay < today:
            date_ebay = datetime.strptime(string_with_date + f' {current_year + 1}', '%a, %b %d %Y').date()

        days_left = (date_ebay - today).days
        return f"{days_left}days"

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
    except ValueError:
        return def_value


def get_columns_map(shop_info):
    try:
        return shop_info['suppliers'][0]['columns']
    except (IndexError, KeyError) as e:
        raise ValueError("Error retrieving columns:")


def get_id_from_link(link_to_table: str):
    return link_to_table.split('/')[5]


def filter_dict(orig_dict: Dict[str, Any], keys: List[str], mode: Literal['remove', 'keep'] = 'remove'):
    if mode not in {'remove', 'keep'}:
        raise ValueError("Invalid mode. Use 'remove' to delete keys or 'keep' to retain keys.")

    if mode == 'remove':
        return {k: v for k, v in orig_dict.items() if k not in keys}
    if mode == 'keep':
        return {k: v for k, v in orig_dict.items() if k in keys}


def processing_qty(data: list, standard_qty: int):
    for i, row in enumerate(data):
        if row['supplier_qty']:
            if int(row['supplier_qty'].replace(',', '')) >= 5:
                data[i]['supplier_qty'] = standard_qty


def prepare_data_for_amz(input_data: List[Dict[str, Any]]):
    new_data = []
    for row_data in input_data:
        row_data['product_id_type'] = 1
        row_data['item_condition'] = 11
        row_data['will_ship_internationally'] = 1
        row_data['add_delete'] = 'a'

        new_data.append(row_data)

    return new_data

