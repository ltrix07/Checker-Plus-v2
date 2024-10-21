import pytest
from checker_plus.parser import EbayParser


@pytest.mark.asyncio
@pytest.mark.parametrize("page_chunk, strategy, expected_result_for_shipping, expected_result_for_proxy_ban", [
    ("<span>This item does not ship to USA</span>", "drop", True, False),
    ("<span>This item does not ship to United States</span>", "drop", True, False),
    ("<span>This item shipping from USA</span>", "drop", False, False),
    ("<span>This item does not ship to USA</span>", "listings", False, False),
    ("<span>This item does not ship to United States</span>", "listings", False, False),
    ("<span></span>", "listings", False, False),
    ("<span></span>", "drop", False, False),
    ("<span>This item does not ship to United Kingdom</span>", "listings", False, True),
    ("<span>This item does not ship to United Kingdom</span>", "drop", False, True),
])
async def test_look_not_shipping_to_usa_trigger(page_chunk, strategy, expected_result_for_shipping,
                                                         expected_result_for_proxy_ban):
    parser = EbayParser(page_chunk)
    await parser.look_not_shipping_to_usa_trigger(strategy=strategy)
    assert parser.not_send_to_usa is expected_result_for_shipping
    assert parser.proxy_ban is expected_result_for_proxy_ban
