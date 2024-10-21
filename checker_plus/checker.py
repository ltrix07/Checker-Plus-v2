import logging
import random
import aiohttp
import asyncio
from typing import List, Dict, Literal
from checker_plus.utils import can_be_type, read_json, logger_message_create
from checker_plus.parser import EbayParser
from aiohttp import BasicAuth
from aiohttp import client_exceptions
from pathlib import Path


class Checker:
    CURRENT_DIR = Path(__file__).parent

    def __init__(self, proxies: list, user_agents: list, shop_config: dict,
                 exceptions: list, exceptions_repricer: list):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.proxies = proxies
        self.user_agents = user_agents
        self.shop_config = shop_config
        self.exceptions = exceptions
        self.exceptions_repricer = exceptions_repricer
        self.report = {
            "all_processed": 0,
            "nones_new": 0,
            "stock_new": 0,
            "new_price": 0,
            "new_ship_price": 0,
            "errors": {
                "unknown": 0,
                "no_block_with_info": 0,
                "proxy_errors": 0,
                "time_out_errors": 0,
                "server_close_connection": 0,
                "site_close_connection": 0,
                "400": 0,
                "404": 0
            },
        }

        self.headers_settings = read_json(self.CURRENT_DIR.parent / "db" / "#general" / "headers_settings.json")
        self.indices = None

    async def define_columns_indices(self, headers: list) -> None:
        indices = {}
        columns: dict = self.shop_config.get("columns")
        for column_key, column_name in columns.items():
            if column_name in headers:
                indices[column_key] = headers.index(column_name)
        self.indices = indices

    async def prepare_data(self, data: list):
        if not self.indices:
            self.logger.warning("No method was called to define the indexes."
                                "You should first call the method 'define_columns_indices'")
            return

        price_index = self.indices.get("supplier_price")
        shipping_index = self.indices.get("supplier_shipping")
        quantity_index = self.indices.get("supplier_quantity")
        for i, row in enumerate(data):
            price = row[price_index] if price_index else None
            shipping = row[shipping_index] if shipping_index else None
            quantity = row[quantity_index] if quantity_index else None
            if price and not can_be_type(price, float):
                self.logger.warning(logger_message_create(i, price, "float"))
                data[i][price_index] = 0
                data[i][shipping_index] = 0
                data[i][quantity_index] = 0
                continue
            elif shipping and not can_be_type(shipping, float):
                self.logger.warning(logger_message_create(i, shipping, "float"))
                data[i][price_index] = 0
                data[i][shipping_index] = 0
                data[i][quantity_index] = 0
                continue
            elif quantity and not can_be_type(quantity, int):
                self.logger.warning(logger_message_create(i, quantity, "int"))
                data[i][price_index] = 0
                data[i][shipping_index] = 0
                data[i][quantity_index] = 0
                continue
        c = 1

    async def prepare_links(self, data: list, marketplace: str):
        if not self.indices:
            raise Exception("In order to call this method you first need to define column indices using the method "
                            "'define_columns_indices()'")
        link_index = self.indices.get("supplier_link")
        supplier_index = self.indices.get("supplier_name")
        for i, row in enumerate(data):
            link = row[link_index]
            if link is None or link == '':
                data[i][supplier_index] = "{no_link}"
            elif marketplace not in link:
                data[i][supplier_index] = "{not_" + marketplace + "_link}"

    async def data_proc(self, data: list, batch_size: int = 100):
        self.logger.info(f"Split the data into parts by {batch_size} pieces")
        data_processed = {}
        piece = 1
        for i in range(0, len(data), batch_size):
            data_processed[piece] = data[i:i + batch_size]
            piece += 1

        return data_processed

    @staticmethod
    async def proxy_auth(proxy: str) -> tuple:
        username = proxy.split(':')[0]
        password = proxy.split(':')[1].split('@')[0]
        host_and_port = proxy.split('@')[1]

        proxy_url = 'http://' + host_and_port
        proxy_auth = BasicAuth(username, password)

        return proxy_url, proxy_auth

    async def request(self, link: str, proxy: dict):
        async with aiohttp.ClientSession() as session:
            try:
                if not proxy:
                    self.logger.warning("No proxy specified.")
                    proxy_url = None
                    proxy_auth = None
                else:
                    proxy_url = proxy["url"]
                    proxy_auth = proxy["auth"]
                async with session.get(
                    link, proxy=proxy_url, proxy_auth=proxy_auth, headers=self.headers_settings
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    if response.status == 400:
                        self.report["errors"]["400"] += 1
                        return "{400_bad_request}"
                    if response.status == 404:
                        self.report["errors"]["404"] += 1
                        return "{404}"
                    if response.status == 403:
                        self.report["errors"]["site_close_connection"] += 1
                        return "{website_close_connection}"
                    else:
                        self.report["errors"]["unknown"] += 1
                        return "{unknown_error}"
            except TimeoutError:
                self.report["errors"]["time_out_errors"] += 1
                return "{time_out_error}"
            except client_exceptions.ClientProxyConnectionError:
                self.report["errors"]["proxy_errors"] += 1
                return "{proxy_error}"
            except client_exceptions.ClientConnectorError:
                self.report["errors"]["proxy_errors"] += 1
                return "{proxy_error}"
            except client_exceptions.ClientOSError:
                self.report["errors"]["proxy_errors"] += 1
                return "{proxy_error}"
            except client_exceptions.ServerConnectionError:
                await asyncio.sleep(5)
                self.report["errors"]["server_close_connection"] += 1
                return "{server_close_connection}"
            except client_exceptions.ContentTypeError:
                self.report["errors"]["400"] += 1
                return "{400_bad_request}"
            except client_exceptions.ClientResponseError:
                self.report["errors"]["website_close_connection"] += 1
                return "{website_close_connection}"

    async def fetch(self, row: list, proxy: dict):
        current_row_data = {
            "sku": row[self.indices.get("sku")],
            "supplier_price": row[self.indices.get("supplier_price")],
            "supplier_shipping": row[self.indices.get("supplier_shipping")],
            "supplier_qty": row[self.indices.get("supplier_qty")],
            "supplier_days": row[self.indices.get("supplier_days")],
            "supplier_name": row[self.indices.get("supplier_name")],
            "variation": True if row[self.indices.get("variation")] == "TRUE" else False,
            "page": None
        }
        if current_row_data["sku"] in self.exceptions:
            return "exception"

        current_row_data["page"] = await self.request(link, proxy)
        return current_row_data

    async def get_pages(self, data: list, batch_size: int = 10):
        proxy_auth_data = []
        result = []
        self.logger.info("Authorization proxies")
        for proxy in self.proxies:
            proxy_url, proxy_auth = await self.proxy_auth(proxy)
            proxy_auth_data.append({"url": proxy_url, "auth": proxy_auth})

        while data:
            tasks = []
            current_batch = data[:batch_size]
            data = data[batch_size:]

            for row in current_batch:
                if self.user_agents:
                    self.headers_settings["user-agent"] = random.choice(self.user_agents)
                if proxy_auth_data:
                    proxy = random.choice(proxy_auth_data)
                else:
                    proxy = None
                tasks.append(self.fetch(row, proxy))
            result.extend(await asyncio.gather(*tasks))
        return result


class EbayChecker(Checker):
    def __init__(self, data: list, proxies: list, user_agents: list, shop_config: dict,
                 exceptions: list, exceptions_repricer: list):
        super().__init__(proxies, user_agents, shop_config, exceptions, exceptions_repricer)
        self.data = data
        self.strategy: Literal["drop", "listings"] = shop_config.get("strategy")

        self.data_by_pieces: dict = None
        self.checked: List[Dict] = []

    async def parsing_page(self, item_data: dict):
        page = item_data.get("page")
        
        parser = EbayParser()
        what_need_to_parse = self.shop_config.get("what_need_to_parse")
        await asyncio.gather(
            parser.look_out_of_stock_triggers(),
            parser.look_pick_up_trigger(),
            parser.look_catalog_trigger(),
            parser.look_not_shipping_to_usa_trigger(self.strategy),
            parser.look_variation_trigger()
        )

    async def start_check(self):
        if not self.indices:
            raise Exception("For using this method you must to use 'define_columns_indices'")
        
        self.logger.info("Starting check data")
        self.data_by_pieces = await self.data_proc(self.data)

        for piece, data_list in self.data_by_pieces.items():
            self.logger.info(f"Checking {piece} piece of data")
            self.logger.info("Checking links before sending requests")
            await self.prepare_links(data_list, 'ebay')
            await self.prepare_data(data_list)
            pages = await self.get_pages(data_list)

    async def end_check(self):
        self.logger.info("Check was end. Cleaning cech...")
        self.data_by_pieces = None
        self.checked = []
        self.proxies = None
        self.user_agents = None
        self.shop_config = None
        self.indices = None


