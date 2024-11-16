import pytest
from checker_plus.utils import get_next_batch


@pytest.mark.parametrize("data, batch_size, expect_remaining_keys, expect_batch_keys", [
    (
        [
            dict(sku="sku1", supplier_price=13.78, supplier_quantity=23, supplier_name="Bob"),
            dict(sku="sku2", supplier_price=31.23, supplier_quantity=3223, supplier_name="Jimm"),
            dict(sku="sku3", supplier_price=100, supplier_quantity=23, supplier_name="Jimm")
        ],
        1,
        ["sku2", "sku3"],
        ["sku1"]
    ),
    (
        [
            dict(sku="sku1", supplier_price=13.78, supplier_quantity=23, supplier_name="Bob"),
            dict(sku="sku2", supplier_price=31.23, supplier_quantity=3223, supplier_name="Jimm"),
            dict(sku="sku3", supplier_price=100, supplier_quantity=23, supplier_name="Jimm")
        ],
        2,
        ["sku3"],
        ["sku1", "sku2"]
    ),
    (
        [
            dict(sku="sku1", supplier_price=13.78, supplier_quantity=23, supplier_name="Bob"),
            dict(sku="sku2", supplier_price=31.23, supplier_quantity=3223, supplier_name="Jimm"),
            dict(sku="sku3", supplier_price=100, supplier_quantity=23, supplier_name="Jimm")
        ],
        4,
        [],
        ["sku1", "sku2", "sku3"]
    )
])
def test_get_next_batch(data, batch_size, expect_remaining_keys, expect_batch_keys):
    batch = get_next_batch(data, batch_size)
    batch_keys = [elem["sku"] for elem in batch]
    data_keys = [elem["sku"] for elem in data]
    assert batch_keys == expect_batch_keys
    assert data_keys == expect_remaining_keys
