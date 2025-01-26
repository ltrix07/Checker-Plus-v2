from services.amazon_manager import get_shipping_ids, get_access_token


def test_get_shipping_ids():
    access_token = get_access_token(
        "amzn1.application-oa2-client.562b5e09d1dd47dfb606f0c6db5af3d5",
        "amzn1.oa2-cs.v1.14579b8a3f6f5b2ca9b2a3238754fc9c2864b16ffec4c0022e71c512089cbf4e",
        "Atzr|IwEBIH3Pmz9ADWulC3m7neD0lTqtJwsqUdLHu_nKxc84Ta_YHbjK2XUjcfJFXHUyR84wjrLdAw068pZmse4qa2E6GtIEX4_2xc4SZgy-32HoI_tUsDkgWSGD-_Mk5fCtqHn0SUw2ossEf-S7DuEbRjxBi3E4Je6-36kTC5XDHH9txEhy47_yzaw3FudwtYqMaSMY2GHwIOPGYncoeBbuyLqpZmLWFmgNr5j1uwX5jlgM5kDL2UtvKGakxCYfcLqplyK13z2RQfaJuNjUrgW8cj7aTbpmyoIyFiaA_I8MV0PRBxLfYjTy9NlDXs5q1jJLJvYLXiExaZEgDPKQuT6lzZnTDY2m"
    )
    shipping_ids = get_shipping_ids(
        access_token, 'A2WJECKVD69FO2'
    )

    print(shipping_ids)


test_get_shipping_ids()
