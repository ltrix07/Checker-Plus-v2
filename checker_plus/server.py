import websockets
import json
import base64
from typing import Literal
from checker_plus.utils import read_json
from checker_plus.api_proxy import SpaceProxy


class ServerHandler:
    def __init__(self):
        server_data = read_json('./db/#general/host_data.json')
        self.host = server_data.get('host')
        self.port = server_data.get('port')

    async def websocket_handler(self, data: dict | list):
        async with websockets.connect(f'ws://{self.host}:{self.port}') as websocket:
            await websocket.send(json.dumps(data))
            response = json.loads(await websocket.recv())
            await websocket.close()
        return response

    async def get_proxies(self, type_prox: str):
        data = {
            'message_type': f'get_proxy_all_{type_prox}'
        }

        return await self.websocket_handler(data)

    async def send_message(self, text: str, shop_name: str):
        data = {
            'message_type': 'send_custom_error',
            'shop_name': shop_name,
            'message_text': text
        }

        return await self.websocket_handler(data)

    async def post_error(self, error_message: str, shop: str):
        data = {
            'message_type': 'error',
            'shop_name': shop,
            'error_text': str(error_message)
        }

        return await self.websocket_handler(data)

    async def post_report(self, shop: str, report: dict,
                          average_time_by_link: float, time_of_code_processing: float, proxies):
        data = {
            'message_type': 'send_report_text',
            'shop_name': shop,
            'all_processed': report['all_processed'],
            'nones_new': report['nones_new'],
            'stock_new': report['stock_new'],
            'new_price': report['new_price'],
            'new_shipping': report['new_ship_price'],
            'errors': report['errors'],
            'bad_info_perc': round(report['errors']['proxy_errors'] / report['all_processed'], 2),
            'average_time_for_processing_link': average_time_by_link,
            'time_of_code_processing': time_of_code_processing,
            'proxies': proxies
        }

        return await self.websocket_handler(data)

    async def send_file(self, message_type: str, caption: str, file_path: str):
        with open(file_path, 'rb') as file:
            data = file.read()
            encoded_data = base64.b64encode(data).decode('utf-8')
            message = {
                "message_type": message_type,
                "caption": caption,
                "file_name": file_path.split('/')[-1],
                "file": encoded_data
            }

        return await self.websocket_handler(message)


async def collect_proxies(service_name: Literal['space_proxy', 'default'] = 'default',
                          api_key: str | None = None,
                          proxy_type: str | None = None):
    if service_name == 'space_proxy' and api_key:
        space_proxy = SpaceProxy(api_key)
        response = space_proxy.get_proxy_list()
        proxies_obj = response.get('results', {})
        return [f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port_http']}" for proxy in proxies_obj]
    server = ServerHandler()
    response = await server.get_proxies(proxy_type)
    proxies_obj = response.get('data', {}).get('proxies', [])
    return [f"{proxy['login']}:{proxy['password']}@{proxy['ip']}:{proxy['port_http']}" for proxy in proxies_obj]
