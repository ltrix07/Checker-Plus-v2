import pytest


@pytest.fixture
def define_columns():
    return {
        "supplier_link": "supplier link",
        "supplier_price": "supplier price",
        "supplier_shipping": "shipping",
        "supplier_quantity": "stock",
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
