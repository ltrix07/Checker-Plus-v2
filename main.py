import os
import asyncio
import time
from services.google_sheet_manager import GoogleSheetManager
from checker_plus.checker import EbayChecker
from checker_plus.utils import read_json, get_id_from_link, filter_dict, processing_qty, prepare_data_for_amz
from checker_plus.server import collect_proxies
from checker_plus.cache_handler import CSV, TXT
from checker_plus.amz_api import AmazonAPI
from set_config import collect_tables_url_from_main_sheet

START_ROW = 1
TABLE_ROW_SIZE = 50000

GOOGLE_CREDS_PH = os.path.join('db', '#general', 'oAuth_creds.json')
SHOP_DATA_PH = os.path.join('db', '#general', 'shop_data.json')
USER_AGENTS_PH = os.path.join('db', '#general', 'user_agents.json')
PROCESSING_PH = os.path.join('processing', 'process.csv')
ERRORS_PH = os.path.join('processing', 'errors.csv')


async def main():
    global START_ROW
    global TABLE_ROW_SIZE
    config = read_json(SHOP_DATA_PH)

    sheet_manager = GoogleSheetManager(creds_dir=GOOGLE_CREDS_PH)

    while True:
        for shop_info in config:
            shop_name = shop_info.get('shop_name')
            main_worksheet = shop_info.get('worksheet')
            columns_map = shop_info.get('columns')
            supplier_marketplace = shop_info.get('supplier_marketplace')
            exceptions_sheet_name = shop_info.get('exceptions_sheet')
            exceptions_repricer_sheet_name = shop_info.get('exceptions_sheet_repricer')
            standard_qty = shop_info.get('qty_on_shop')
            amz_creds = shop_info.get('amz_creds')

            print(f'Start check {shop_name}')

            table_id_list = collect_tables_url_from_main_sheet(shop_name)

            for table_link in table_id_list:
                start_time = time.time()
                if not table_link:
                    continue
                print(f'Checking table with data {START_ROW} - {TABLE_ROW_SIZE}')

                proc_file = CSV(PROCESSING_PH, True)
                errors_file = CSV(ERRORS_PH, True)
                proc_file.create_file(columns_map)
                errors_file.create_file(["sku", "error_type"])

                table_id = get_id_from_link(table_link)

                inventory_data = sheet_manager.get_sheet_data(
                    spreadsheet_id=table_id,
                    worksheet_name=main_worksheet,
                    columns_map=columns_map
                )
                exceptions_data = [sku['sku'] for sku in sheet_manager.get_sheet_data(
                    spreadsheet_id=table_id,
                    worksheet_name=exceptions_sheet_name,
                    columns_map={'sku': 'SKU'}
                )]
                exceptions_repricer_data = [sku['sku'] for sku in sheet_manager.get_sheet_data(
                    spreadsheet_id=table_id,
                    worksheet_name=exceptions_repricer_sheet_name,
                    columns_map={'sku': 'SKU'}
                )]

                proxies = await collect_proxies('space_proxy',
                                                '9A1TISnmV0UmHTwQ0af5sY8GOKDgwJiMeJXD4cAR')
                user_agents_list = read_json(USER_AGENTS_PH)

                if supplier_marketplace == 'ebay':
                    checker = EbayChecker(
                        data=inventory_data,
                        proxies=proxies,
                        user_agents=user_agents_list,
                        shop_config=shop_info,
                        exceptions=exceptions_data,
                        exceptions_repricer=exceptions_repricer_data,
                        cache_path=proc_file,
                        errors_path=errors_file
                    )
                else:
                    print('You specified wrong supplier marketplace')
                    continue

                await checker.start_check(batch_size=10)
                await checker.end_check()

                checked_data = proc_file.read()

                columns_map_filtered = filter_dict(columns_map, ['our_price', 'our_shipping', 'handling_time',
                                                                 'merchant_shipping'])
                sheet_manager.update_sheet_data_by_sku(
                    spreadsheet_id=table_id,
                    worksheet_name=main_worksheet,
                    data=checked_data,
                    columns_map=columns_map_filtered,
                    sku_column=columns_map['sku']
                )

                columns_map_filtered = filter_dict(columns_map,
                                                   ['asin', 'sku', 'our_price', 'supplier_qty', 'handling_time',
                                                    'merchant_shipping'],
                                                   'keep')
                updated_data = sheet_manager.get_sheet_data(
                    spreadsheet_id=table_id,
                    worksheet_name=main_worksheet,
                    columns_map=columns_map_filtered
                )
                processing_qty(updated_data, standard_qty)

                columns_to_amz = ['sku', 'price', 'quantity', 'handling-time',
                                  'merchant_shipping_group_name']
                to_amz_file = TXT('./uploads/upload.txt', True)
                to_amz_file.create_file(columns_to_amz)

                columns_map_amz = {
                    'sku': 'sku',
                    'our_price': 'price',
                    'supplier_qty': 'quantity',
                    'handling_time': 'handling-time',
                    'merchant_shipping': 'merchant_shipping_group_name'
                }
                to_amz_file.append_to_file(updated_data, columns_map_amz)

                amz_api = AmazonAPI(amz_creds)
                status = amz_api.upload_to_amz('./uploads/upload.txt')
                end_time = time.time()

                total_time = (end_time - start_time) / 60 / 60
                print(status)
                print(total_time)

                START_ROW += TABLE_ROW_SIZE
                TABLE_ROW_SIZE += TABLE_ROW_SIZE

            START_ROW = 1
            TABLE_ROW_SIZE = 50000


if __name__ == '__main__':
    asyncio.run(main())
