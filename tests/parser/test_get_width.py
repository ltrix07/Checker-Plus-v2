import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_width_valid(valid_html):
    parser = EbayParser(valid_html)
    width = await parser.get_width()
    assert width == "test width"


@pytest.mark.asyncio
async def test_get_voltage_empty(empty_html):
    parser = EbayParser(empty_html)
    width = await parser.get_width()
    assert width is None
