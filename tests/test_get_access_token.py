from services.amazon_manager import get_access_token


def test_get_access_token():
    token = get_access_token()

    print(token)


if __name__ == '__main__':
    test_get_access_token()
