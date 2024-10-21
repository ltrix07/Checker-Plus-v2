import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_look_out_of_stock_triggers_valid(valid_html):
    parser = EbayParser(valid_html)
    await parser.look_out_of_stock_triggers()
    assert parser.out_of_stock is True


@pytest.mark.asyncio
async def test_look_out_of_stock_triggers_empty(empty_html):
    parser = EbayParser(empty_html)
    await parser.look_out_of_stock_triggers()
    assert parser.out_of_stock is False
