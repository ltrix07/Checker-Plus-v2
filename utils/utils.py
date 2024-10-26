# utils.py
import os
import json


def load_json_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8-sig') as file:
        return json.load(file)


def get_columns_map(shop_info):
    try:
        return shop_info['suppliers'][0]['columns']
    except (IndexError, KeyError) as e:
        raise ValueError("Error retrieving columns:")
