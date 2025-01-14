import re
from services.google_sheet_manager import GoogleSheetManager
from checker_plus.cache_handler import CSV
from set_config import collect_tables_url_from_main_sheet
from checker_plus.utils import get_id_from_link


def sort_by_sku(data: list, sku_key: str):
    def extract_numeric_part(sku):
        match = re.search(r'\d+$', sku)
        return int(match.group()) if match else 0

    return sorted(data, key=lambda x: extract_numeric_part(x[sku_key]))


def split_into_batches(data, batch_size: int = 50000):
    return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]


def start(shop_name: str):
    count = 1

    sheet_manager = GoogleSheetManager('./db/#general/oAuth_creds.json')
    columns = {
        "asin": "asin",
        "sku": "sku",
        "listing_link": "link",
        "our_price": "price amazon",
        "our_shipping": "amazon shipping",
        "supplier_link": "supplier1",
        "supplier_price": "price ebay",
        "supplier_shipping": "shipping",
        "supplier_qty": "stock",
        "supplier_days": "shipping days",
        "supplier_name": "supplier name",
        "variation": "variation",
        "part_number": "mpn",
        "item_weight": "weight",
        "product_dimensions": "dimensions",
        "color": "color",
        "unit_count": "unit count",
        "material_type": "material type",
        "power_source": "power source",
        "voltage": "voltage",
        "wattage": "wattage",
        "included_components": "included components",
        "speed": "speed",
        "number_of_boxes": "number of boxes",
        "title": "title",
        "description": "description"
    }

    csv = CSV('./data_for_filter.csv')
    # csv.create_file(columns)
    #
    sheets_links = collect_tables_url_from_main_sheet(shop_name)
    #
    # for link in sheets_links:
    #     sheet_id = get_id_from_link(link)
    #     data_from_sheet = sheet_manager.get_sheet_data(
    #         spreadsheet_id=sheet_id,
    #         worksheet_name='INVENTORY',
    #         columns_map=columns
    #     )
    #
    #     csv.append_to_file(data_from_sheet, columns)
    #     print(f"Looking {count} table")
    #     count += 1
    #
    # data_from_csv = csv.read()
    # sorted_data = sort_by_sku(data_from_csv, 'sku')
    #
    # csv.clear()
    # csv.append_to_file(sorted_data, columns)

    data_from_csv = csv.read()
    splat_data = split_into_batches(data_from_csv)

    for i, data in enumerate(splat_data):
        sheet_id = get_id_from_link(sheets_links[i])
        sheet_manager.update_sheet_data(
            spreadsheet_id=sheet_id,
            worksheet_name='INVENTORY',
            columns_map=columns,
            data=data
        )
        print(f'Updating data {i + 1}')


if __name__ == '__main__':
    start('Tatiana')




