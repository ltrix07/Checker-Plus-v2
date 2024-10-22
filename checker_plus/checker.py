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

        self.auth_proxies: List[dict] = []

    async def proxy_auth(self) -> None:
        for proxy in self.proxies:
            username = proxy.split(':')[0]
            password = proxy.split(':')[1].split('@')[0]
            host_and_port = proxy.split('@')[1]

            proxy_url = 'http://' + host_and_port
            proxy_auth = BasicAuth(username, password)

            self.auth_proxies.append({"url": proxy_url, "auth": proxy_auth})

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

    async def get_pages(self, data: Dict[str, dict], batch_size: int = 10):
        result = []
        self.logger.info("Authorization proxies")
        if not self.proxies:
            raise Exception("No proxy was specified. In order to continue code execution you need to "
                            "specify a set of proxies in the format: "
                            "[{'url': proxy_url1, 'auth': proxy_auth1}, {'url': proxy_url2, 'auth': proxy_auth2}]")
        await self.proxy_auth()

        while data:
            tasks = []
            current_batch = data[:batch_size]
            data = data[batch_size:]

            for row in current_batch:
                if self.user_agents:
                    self.headers_settings["user-agent"] = random.choice(self.user_agents)
                proxy = random.choice(self.auth_proxies)
                tasks.append(self.fetch(row, proxy))
            result.extend(await asyncio.gather(*tasks))
        return result


class EbayChecker(Checker):
    def __init__(self, data: Dict[str, dict], proxies: list, user_agents: list, shop_config: dict,
                 exceptions: list, exceptions_repricer: list):
        super().__init__(proxies, user_agents, shop_config, exceptions, exceptions_repricer)
        self.data: Dict[str, dict] = data
        self.strategy: Literal["drop", "listings"] = shop_config.get("strategy")
        self.checked: List[Dict] = []

    async def parsing_page(self, item_data: dict):
        page = item_data.get("page")
        
        parser = EbayParser(page=page)
        what_need_to_parse = self.shop_config.get("what_need_to_parse")
        await asyncio.gather(
            parser.look_out_of_stock_triggers(),
            parser.look_pick_up_trigger(),
            parser.look_catalog_trigger(),
            parser.look_not_shipping_to_usa_trigger(self.strategy),
            parser.look_variation_trigger()
        )

    async def start_check(self):
        self.logger.info("Start checking data")

        pages = self.get_pages(self.data)

    async def end_check(self):
        self.logger.info("Check was end. Cleaning cech...")
        self.checked = []
        self.proxies = None
        self.user_agents = None
        self.shop_config = None
