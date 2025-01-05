import requests


class SpaceProxy():
    def __init__(self, api_key: str):
        self.api_link = 'https://panel.spaceproxy.net/api/'
        self.api_key = api_key

    def get_proxy_list(self, params: dict | None = None):
        return requests.get(f'{self.api_link}proxies/?api_key={self.api_key}', params=params).json()
