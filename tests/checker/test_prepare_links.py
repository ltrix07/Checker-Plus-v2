import asyncio
from checker_plus.checker import Checker


async def test_prepare_links():
    config = {
        "columns": {
            "supplier_link": "supplier",
            "supplier_price": "supplier price",
            "supplier_shipping": "shipping",
            "supplier_qty": "stock",
            "supplier_days": "shipping days",
            "supplier_name": "supplier name",
            "variation": "variation",
            "part_number": "mpn",
            "item_weight": "weight",
            "product_dimensions": "dimensions",
            "color": "color",
            "unit_count": "unit count",
            "material_type": "material type",
            "power_source": "power source",
            "voltage": "voltage",
            "wattage": "wattage",
            "included_components": "included components",
            "speed": "speed",
            "number_of_boxes": "number of boxes",
            "title": "title",
            "description": "description"
        }
    }
    checker = Checker([], [], config, [], [])
    data = [
        ["supplier", "supplier name"],
        ["amazon.com", "Jimmy"],
        ["ebay.com", "Bobby"],
        ["", "Brandon"]
    ]
    await checker.define_columns_indices(data[0])
    await checker.prepare_links(data, "ebay")
    print(data)


asyncio.run(test_prepare_links())