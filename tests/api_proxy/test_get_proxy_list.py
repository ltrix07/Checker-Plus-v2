from checker_plus.api_proxy import SpaceProxy


def test_get_proxy_list():
    space_proxy = SpaceProxy('9A1TISnmV0UmHTwQ0af5sY8GOKDgwJiMeJXD4cAR')
    proxies = space_proxy.get_proxy_list()
    print(proxies)


test_get_proxy_list()
