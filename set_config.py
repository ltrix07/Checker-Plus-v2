from checker_plus.utils import read_json, write_json
from checker_plus import MAIN_SHEET_CONF
from services.google_sheet_manager import GoogleSheetManager


def add_columns(standard_cols: dict) -> dict:
    while True:
        key = input('Enter column key ("q" to exit): ').strip()
        if key == 'q':
            break
        value = input('Enter column value ("q" to exit): ').strip()
        if value == 'q':
            break
        standard_cols[key] = value

    return standard_cols


def get_choice(prompt, options):
    while True:
        choice = input(prompt).strip()
        if choice in options:
            return choice
        print('Invalid choice, please try again.')


def collect_tables_url_from_main_sheet(shop_name: str):
    main_table_id = MAIN_SHEET_CONF.get('table_id')
    main_sheet_name = MAIN_SHEET_CONF.get('sheet_name')
    sheet_manager = GoogleSheetManager('./db/#general/credentials.json')
    links = sheet_manager.get_sheet_data(
        spreadsheet_id=main_table_id,
        worksheet_name=main_sheet_name,
        columns_map={'shop': shop_name}
    )
    print(links)
    return [row['shop'] for row in links]


def add_shop():
    while True:
        try:
            shop_name = input('Enter shop name: ').strip()
            choice_marketplace = get_choice(
                'Choose supplier marketplace:\n1. Ebay\n2. Amazon\n3. HomeDepot\n',
                {'1', '2', '3'}
            )
            supplier_marketplace = {'1': 'ebay', '2': 'amazon', '3': 'homedepot'}[choice_marketplace]
            append_columns = read_json(f'./db/{supplier_marketplace}/standard_columns.json')

            standard_columns = read_json('./db/#general/standard_columns.json')
            standard_need_to_parse = read_json('./db/#general/what_need_to_parse.json')

            print('Do you want to modify standard columns?')
            if get_choice('1. Yes\n2. No\n', {'1', '2'}) == '1':
                standard_columns = add_columns(standard_columns)

            print('Do you want to modify append columns?')
            if get_choice('1. Yes\n2. No\n', {'1', '2'}) == '1':
                append_columns = add_columns(append_columns)

            standard_columns = {**standard_columns, **append_columns}

            worksheet = input("Enter worksheet name: ").strip()
            standard_qty_on_shop = int(input('Enter standard qty on shop: ').strip())

            exceptions_sheet = input('Enter exceptions sheet name (empty to skip): ').strip() or None
            exceptions_sheet_repricer = input('Enter exceptions sheet repricer name (empty to skip): ').strip() or None

            print('Do you want to modify what to parse?')
            if get_choice('1. Yes\n2. No\n', {'1', '2'}) == '1':
                standard_need_to_parse = add_columns(standard_need_to_parse)

            strategy = {'1': 'drop', '2': 'listings'}[get_choice('1. BrandDrop\n2. Listings\n', {'1', '2'})]

            amz_creds = {
                'lwa_app_id': input('Enter lwa_app_id: ').strip(),
                'lwa_client_secret': input('Enter lwa_client_secret: ').strip(),
                'refresh_token': input('Enter refresh_token: ').strip()
            }

            shop_inf = read_json('./db/#general/shop_data.json')
            shop_inf.append({
                'shop_name': shop_name,
                'worksheet': worksheet,
                'columns': standard_columns,
                'supplier_marketplace': supplier_marketplace,
                'qty_on_shop': standard_qty_on_shop,
                'exceptions_sheet': exceptions_sheet,
                'exceptions_sheet_repricer': exceptions_sheet_repricer,
                'what_need_to_parse': standard_need_to_parse,
                'strategy': strategy,
                'amz_creds': amz_creds
            })
            write_json('./db/#general/shop_data.json', shop_inf)
            print("Shop added successfully.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue


if __name__ == '__main__':
    print('1. Add shop\n'
          '2. Delete shop\n')
    action = input('Choose action: ')
    if action == '1':
        add_shop()
    elif action == '2':
        pass
    else:
        print('Invalid command')
