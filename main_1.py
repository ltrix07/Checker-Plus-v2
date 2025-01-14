import os
import json
from services.google_sheet_manager import GoogleSheetManager
from checker_plus.utils import read_json, get_columns_map


def get_links_from_conf():
    pass


def main():
    # shop_data_file = os.path.join('db', '#general', 'shop_data.json')
    # json_data = read_json(shop_data_file)

    # sheet_manager = GoogleSheetManager()

    # shop_info = json_data[0]
    # columns_map = get_columns_map(shop_info)
    # spreadsheet_id = shop_info['table_link']
    # worksheet_name = shop_info['worksheet']

    # data = sheet_manager.get_sheet_data(
    #     spreadsheet_id, worksheet_name, columns_map)
    # fetched_data_file = 'fetched_data.json'
    # with open(fetched_data_file, 'w') as f:
    #     json.dump(data, f, indent=2)
    # print("Data fetched and saved to fetched_data.json")
    # with open(fetched_data_file, 'r') as f:
    #     update_data = json.load(f)

 
    # sheet_manager.update_sheet_data(
    #     spreadsheet_id, worksheet_name, update_data, columns_map)
    # print("Data from fetched_data.json updated back to the sheet")
    spreadsheet_id = '1v5FZsB9kXi4nT3dY3wASJha-kkdpdZM5RoN1aW5v9DM'
    worksheet_name = 'Inventory'
    sku_column = 'sku'
    columns_map = {'SKU': 'sku',
                   'Price': 'price ebay', 'Supplier': 'supplier1'}

    data_to_update = [
        {'SKU': 'Megi1', 'Price': '200', 'Supplier': 'TESTMegi1'},
        {'SKU': 'Megi6', 'Price': '300', 'Supplier': 'TESTMegi6'}
    ]

    sheet_manager = GoogleSheetManager(creds_dir='credentials.json')


    sheet_manager.update_sheet_data_by_sku(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        data=data_to_update,
        sku_column=sku_column,
        columns_map=columns_map,
    )


if __name__ == "__main__":
    main()
