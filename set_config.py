from checker_plus.utils import read_json


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


def collect_tables_url_from_main_sheet(shop_name: str):
    pass


def add_shop():
    standard_qty_on_shop, strategy = None, None
    while True:
        standard_columns = read_json('./db/#general/standard_columns.json')
        standard_need_to_parse = read_json('./db/#general/what_need_to_parse.json')
        shop_name = input('Enter shop name: ').lower().strip()
        print(
            f'{standard_columns}\n'
            f''
            f'Do you want add columns custom or change standard columns?\n'
            f'1. Yes\n'
            f'2. No'
        )
        choice = input('Choose action: ').strip()
        if choice == '1':
            standard_columns = add_columns(standard_columns)
        elif choice == '2':
            pass
        else:
            print("Wrong input")

        worksheet = input("Enter worksheet name: ")

        while True:
            try:
                standard_qty_on_shop = int(input('Enter standard qty on shop: ').strip())
                break
            except ValueError:
                print('Wrong input')

        exceptions_sheet = input('Enter exceptions sheet name (empty to skip): ').strip()
        exceptions_sheet_repricer = input('Enter exceptions sheet repricer name (empty to skip): ').strip()
        if exceptions_sheet == '':
            exceptions_sheet = None
        if exceptions_sheet_repricer == '':
            exceptions_sheet_repricer = None

        print(
            f'{standard_need_to_parse}\n'
            f''
            f'Do you want change what need to parse?\n'
            f'1. Yes\n'
            f'2. No\n'
        )
        choice = input('Choose action: ').strip()
        if choice == '1':
            standard_need_to_parse = add_columns(standard_need_to_parse)
        elif choice == '2':
            pass
        else:
            print('Wrong input')

        print(
            'Strategies:\n'
            '1. BrandDrop\n'
            '2. Listings\n'
        )
        choice = input('Choose strategy: ').strip()
        if choice == '1':
            strategy = 'drop'
        elif choice == '2':
            strategy = 'listings'
        else:
            print('Wrong input')

        amz_creds = {
            'lwa_app_id': input('Enter lwa_app_id: ').strip(),
            'lwa_client_secret': input('Enter lwa_client_secret: ').strip(),
            'refresh_token': input('Enter refresh_token: ').strip()
        }

        shop_inf = read_json('./db/#general/shop_data.json')
        shop_inf.append({

        })

