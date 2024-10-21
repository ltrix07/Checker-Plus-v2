import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_shipping_price_valid(valid_html):
    parser = EbayParser(valid_html)
    shipping_price = await parser.get_shipping_price()
    assert shipping_price == "8.95"


@pytest.mark.asyncio
async def test_get_shipping_price_empty(empty_html):
    parser = EbayParser(empty_html)
    shipping_price = await parser.get_shipping_price()
    assert shipping_price is None
