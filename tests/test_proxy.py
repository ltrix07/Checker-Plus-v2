import requests

proxy_dict = {
    "http": "http://skotarenko138:pTphNcpBUQ@161.77.231.139:59101",
    "https": "http://skotarenko138:pTphNcpBUQ@161.77.231.139:59101"
}

url = "https://www.ebay.com/itm/232770014411?hash=item36322c8ccb:g:xrMAAOSwgFJa-xII&amdata=enc%3AAQAHAAAAwFZFwENRzy7GWBimiUxy%2B4USIW96o1LxBaaNvaj0D8K8UXDe7fVqUsLJli93pBc%2FEVUy%2Fn9xPIE2FKOrwWcQdPeb%2FhOwTic6ShbpLFROql5KCIHzND%2F%2BiBQEekvi%2F0t9PKFVLEGD45nfzjZRfwUOnfR8jlYE4bWpPV3uqu2XWcTJjfq3rpLIs0X3qYLhwr%2BMqbVBloBVAlO4VLV2LU5YwXWLQq2XDBfZYMeTwm7hkvW%2B03GAy9CEcUx%2BwtVso4vOUg%3D%3D%7Ctkp%3ABk9SR_SlitjtYQ"

try:
    response = requests.get(url, proxies=proxy_dict, timeout=10)
    print(response.text)
except requests.exceptions.ProxyError as e:
    print(f"Proxy error: {e}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
except requests.exceptions.Timeout as e:
    print(f"Request timed out: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
