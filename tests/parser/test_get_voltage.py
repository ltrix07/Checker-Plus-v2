import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_get_voltage_valid(valid_html):
    parser = EbayParser(valid_html)
    voltage = await parser.get_voltage()
    assert voltage == "test voltage"


@pytest.mark.asyncio
async def test_get_voltage_empty(empty_html):
    parser = EbayParser(empty_html)
    voltage = await parser.get_voltage()
    assert voltage is None
