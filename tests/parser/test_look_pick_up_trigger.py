import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
async def test_look_pick_up_trigger_valid(valid_html):
    parser = EbayParser(valid_html)
    await parser.look_pick_up_trigger()
    assert parser.pick_up is True


@pytest.mark.asyncio
async def test_look_pick_up_trigger_empty(empty_html):
    parser = EbayParser(empty_html)
    await parser.look_pick_up_trigger()
    assert parser.pick_up is False
