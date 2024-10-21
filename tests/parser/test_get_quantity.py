import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_price_valid(valid_html):
    parser = EbayParser(valid_html)
    quantity = await parser.get_quantity()
    assert quantity == "322"


@pytest.mark.asyncio
async def test_get_price_empty(empty_html):
    parser = EbayParser(empty_html)
    quantity = await parser.get_quantity()
    assert quantity is None
