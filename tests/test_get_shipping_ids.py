from services.amazon_manager import get_shipping_ids, get_access_token


def test_get_shipping_ids():
    access_token = get_access_token()
    shipping_ids = get_shipping_ids(
        access_token, 'A2WJECKVD69FO2'
    )

    print(shipping_ids)


test_get_shipping_ids()
