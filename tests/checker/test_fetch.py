import pytest
from unittest.mock import AsyncMock, patch
from checker_plus.checker import Checker


@pytest.mark.asyncio
@pytest.mark.parametrize("exceptions, item_data, proxy, mock_page, expect_dict", [
    (
        ["sku1"],
        {"sku": "sku1", "supplier_link": "test", "supplier_price": 32.43, "supplier_name": "Jimm"},
        dict(url="http://test.com", auth="auth_data"),
        None,
        {"sku": "sku1", "supplier_link": "test", "supplier_price": 32.43, "supplier_name": "Jimm", "page": None}
    ),
    (
        ["sku1"],
        {"sku": "sku2", "supplier_link": "test", "supplier_price": 32.43, "supplier_name": "Jimm"},
        dict(url="http://test.com", auth="auth_data"),
        "<html>Response 200</http>",
        {"sku": "sku2", "supplier_link": "test", "supplier_price": 32.43, "supplier_name": "Jimm",
          "page": "<html>Response 200</http>"}
    )
])
async def test_fetch(exceptions, item_data, proxy, mock_page, expect_dict):
    with patch("checker_plus.checker.Checker.request", new=AsyncMock(return_value=mock_page)):
        checker = Checker({}, [], [], {}, exceptions, [])
        row_data = await checker.fetch(item_data, proxy)
        assert row_data == expect_dict
