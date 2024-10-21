import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_look_variation_trigger_valid(valid_html):
    parser = EbayParser(valid_html)
    await parser.look_variation_trigger()
    assert parser.variation is True


@pytest.mark.asyncio
async def test_look_variation_trigger_empty(empty_html):
    parser = EbayParser(empty_html)
    await parser.look_variation_trigger()
    assert parser.variation is False
