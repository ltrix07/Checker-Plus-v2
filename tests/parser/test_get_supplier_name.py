import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_supplier_name_valid(valid_html):
    parser = EbayParser(valid_html)
    supplier_name = await parser.get_supplier_name()
    assert supplier_name == "test_supplier"


@pytest.mark.asyncio
async def test_get_supplier_name_empty(empty_html):
    parser = EbayParser(empty_html)
    supplier_name = await parser.get_supplier_name()
    assert supplier_name is None
