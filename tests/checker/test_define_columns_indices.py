import pytest
from checker_plus.checker import Checker


@pytest.mark.asyncio
@pytest.mark.parametrize("headers, expected_result", [
    (["name", "supplier link", "supplier price", "quantity"],
     dict(supplier_link=1, supplier_price=2)),
    (["supplier link", "supplier price", "quantity", "supplier name"],
     dict(supplier_link=0, supplier_price=1, supplier_name=3))
])
async def test_define_columns_indices(headers, expected_result, define_columns):
    config = dict(columns=define_columns)
    checker = Checker([], [], config, [], [])
    await checker.define_columns_indices(headers=headers)
    assert checker.indices == expected_result

