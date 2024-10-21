import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_item_title_valid(valid_html):
    parser = EbayParser(valid_html)
    last_shipping_day = await parser.get_last_shipping_day()
    assert last_shipping_day == "5days"


@pytest.mark.asyncio
async def test_get_item_title_empty(empty_html):
    parser = EbayParser(empty_html)
    last_shipping_day = await parser.get_last_shipping_day()
    assert last_shipping_day is '0days'
