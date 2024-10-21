import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_power_source_valid(valid_html):
    parser = EbayParser(valid_html)
    power_source = await parser.get_power_source()
    assert power_source == "test power source"


@pytest.mark.asyncio
async def test_get_power_source_empty(empty_html):
    parser = EbayParser(empty_html)
    power_source = await parser.get_power_source()
    assert power_source is None
