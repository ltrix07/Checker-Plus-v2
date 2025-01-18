import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from checker_plus.checker import EbayChecker
from checker_plus.cache_handler import CSV


async def test_proxy_error():
    data = [
        {
            'sku': 'sku1',
            'link': 'https://www.ebay.com/itm/115747275012'
        },
        {
            'sku': 'sku2',
            'link': 'https://www.ebay.com/itm/325307668085'
        }
    ]

    proc_file = CSV('./tests/test_process.csv', True)
    error_file = CSV('./tests/test_errors.csv', True)
    proc_file.create_file(['sku', 'link'])
    error_file.create_file(['sku', 'link'])

    checker = EbayChecker(
        data=data,
        proxies=['http://qweqwdqw:qwe2rwed@1.23.322.1:6554'],
        user_agents=[],
        shop_config={'strategy': 'drop'},
        exceptions=[],
        exceptions_repricer=[],
        cache_path=proc_file,
        errors_path=error_file
    )

    await checker.start_check()
    await checker.end_check()


if __name__ == '__main__':
    asyncio.run(test_proxy_error())
