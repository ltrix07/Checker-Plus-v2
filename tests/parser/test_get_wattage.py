import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_wattage_valid(valid_html):
    parser = EbayParser(valid_html)
    wattage = await parser.get_wattage()
    assert wattage == "test wattage"


@pytest.mark.asyncio
async def test_get_voltage_empty(empty_html):
    parser = EbayParser(empty_html)
    wattage = await parser.get_wattage()
    assert wattage is None
