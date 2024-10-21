# import asyncio
# from checker_plus.checker import Checker
#
#
# async def test_prepare_data():
#     config = {
#         "columns": {
#             "supplier_price": "supplier_price",
#             "supplier_shipping": "supplier_shipping",
#             "supplier_quantity": "supplier_quantity",
#             "shipping_days": "shipping_days"
#         }
#     }
#     checker = Checker([], [], config, [], [])
#     data = [
#         ["supplier_price", "supplier_shipping", "supplier_quantity", "shipping_days"],
#         ["3423", "32.03", "43.43", "7days"],
#         ["dsfed", "22.03", "3", "7days"]
#     ]
#     await checker.define_columns_indices(data[0])
#     await checker.prepare_data(data)
#     print(data)
#
#
# asyncio.run(test_prepare_data())


import pytest
from checker_plus.checker import Checker

INDICES = dict(
    supplier_link=0, supplier_price=1, supplier_shipping=2, supplier_qty=3
)


@pytest.mark.asyncio
@pytest.mark.parametrize("data_list, expected_result", [
    ([["test_link2", "frg", 21, 56]], [["test_link2", 0.0, 0.0, 0]]),
    ([["test_link1", 23, 11, 10]], [["test_link1", 23.00, 11.00, 10.00]]),
])
async def test_prepare_data(data_list, expected_result, define_columns):
    config = dict(columns=define_columns)
    checker = Checker([], [], config, [], [])
    checker.indices = INDICES
    await checker.prepare_data(data_list)
    assert data_list == expected_result
