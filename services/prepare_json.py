import json


def generate_json(data, enum_mapping: dict,  default_stock: int):
    messages = []
    for idx, row in enumerate(data):
        sku = row['sku']
        if sku == '':
            continue
        price_amazon = row['our_price']
        stock = int(row['supplier_qty']) if isinstance(
            row['supplier_qty'], str) and row['supplier_qty'].isdigit() else row['supplier_qty']
        handling_time = row['handling_time']
        merchant_shipping_group_name = row['merchant_shipping']

        merchant_shipping_group_uuid = enum_mapping.get(
            merchant_shipping_group_name, merchant_shipping_group_name)

        if stock == 0 or stock == '':
            messages.append({
                "messageId": idx + 1,
                "sku": sku,
                "operationType": "PATCH",
                "productType": "PRODUCT",
                "patches": [
                    {
                        "op": "replace",
                        "path": "/attributes/fulfillment_availability",
                        "value": [
                            {
                                "fulfillment_channel_code": "DEFAULT",
                                "quantity": 0
                            }
                        ]
                    }
                ]
            })
        else:
            messages.append({
                "messageId": idx + 1,
                "sku": sku,
                "operationType": "PATCH",
                "productType": "PRODUCT",
                "patches": [
                    {
                        "op": "replace",
                        "path": "/attributes/fulfillment_availability",
                        "value": [
                            {
                                "fulfillment_channel_code": "DEFAULT",
                                "quantity": stock if stock < 6 else default_stock,
                                "lead_time_to_ship_max_days": handling_time
                            }
                        ]
                    },
                    {
                        "op": "replace",
                        "path": "/attributes/purchasable_offer",
                        "value": [
                            {
                                "currency": "USD",
                                "our_price": [
                                    {
                                        "schedule": [
                                            {
                                                "value_with_tax": price_amazon
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "op": "replace",
                        "path": "/attributes/merchant_shipping_group",
                        "value": [
                            {
                                "value": merchant_shipping_group_uuid
                            }
                        ]
                    }
                ]
            })

    return messages


def split_and_write_json(messages, output_prefix, seller_id, chunk_size=10000):
    for i in range(0, len(messages), chunk_size):
        chunk = messages[i:i + chunk_size]
        result = {
            "header": {
                "sellerId": seller_id,
                "version": "2.0",
                "issueLocale": "en_US"
            },
            "messages": chunk
        }
        output_file = f"./uploads/{output_prefix}_{i // chunk_size + 1}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=4)
