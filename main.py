import os
import asyncio
from services.google_sheet_manager import GoogleSheetManager
from checker_plus.checker import EbayChecker
from checker_plus.utils import read_json, get_id_from_link, filter_dict, processing_qty
from checker_plus.server import collect_proxies
from checker_plus.cache_handler import CSV


TABLE_ROW_SIZE = 50000

GOOGLE_CREDS_PH = os.path.join('db', '#general', 'credentials.json')
SHOP_DATA_PH = os.path.join('db', '#general', 'shop_data.json')
USER_AGENTS_PH = os.path.join('db', '#general', 'user_agents.json')
PROCESSING_PH = os.path.join('processing', 'process.csv')
ERRORS_PH = os.path.join('processing', 'errors.csv')


async def main():
    config = read_json(SHOP_DATA_PH)

    sheet_manager = GoogleSheetManager(creds_dir=GOOGLE_CREDS_PH)

    for shop_info in config:
        table_id_list = [table_id for table_id in shop_info.get('table_link') if table_id != '']
        main_worksheet = shop_info.get('worksheet')
        columns_map = shop_info.get('columns')
        exceptions_sheet_name = shop_info.get('exceptions_sheet')
        exceptions_repricer_sheet_name = shop_info.get('exceptions_sheet_repricer')
        standard_qty = shop_info.get('qty_on_shop')

        for table_link in table_id_list:
            if not table_link:
                continue

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
            checker = EbayChecker(
                data=inventory_data,
                indices=sheet_manager.indices,
                proxies=proxies,
                user_agents=user_agents_list,
                shop_config=shop_info,
                exceptions=exceptions_data,
                exceptions_repricer=exceptions_repricer_data,
                cache_path=PROCESSING_PH,
                errors_path=ERRORS_PH
            )

            await checker.start_check()
            await checker.end_check()

            proc_file = CSV('processing/process.csv')
            checked_data = proc_file.read()

            columns_map_filtered = filter_dict(columns_map, ['our_price', 'handling_time', 'merchant_shipping'])
            sheet_manager.update_sheet_data(
                spreadsheet_id=table_id,
                worksheet_name=main_worksheet,
                data=checked_data,
                columns_map=columns_map_filtered
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


if __name__ == '__main__':
    asyncio.run(main())
