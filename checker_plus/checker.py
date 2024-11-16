import logging
import random
import aiohttp
import asyncio
from typing import List, Dict, Literal, Any
from checker_plus.utils import read_json, get_next_batch, retype
from checker_plus.parser import EbayParser
from aiohttp import BasicAuth
from aiohttp import client_exceptions
from pathlib import Path


class Checker:
    CURRENT_DIR = Path(__file__).parent

    def __init__(self, indices: Dict[str, int], proxies: list, user_agents: list, shop_config: dict,
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

        self.headers_settings = None

        self.auth_proxies: List[dict] = []
        self.indices = indices

    def __call__(self, *args, **kwargs):
        try:
            self.headers_settings = read_json(self.CURRENT_DIR.parent / "db" / "#general" / "headers_settings.json")
        except FileNotFoundError:
            pass

    async def proxy_auth(self) -> None:
        for proxy in self.proxies:
            if "@" not in proxy or ":" not in proxy:
                raise TypeError(f"Your proxy must be type 'login:password@ip:port' you specified '{proxy}'")
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

    async def fetch(self, item_data: Dict[str, Any], proxy: dict):
        sku = item_data.get("sku")
        if sku in self.exceptions or sku == '' or not sku:
            item_data["page"] = None
            return item_data
        link = item_data.get("supplier_link")

        item_data["page"] = await self.request(link, proxy)
        return item_data

    async def get_pages(self, data: List[Dict[str, Any]], batch_size: int = 5) -> tuple[Dict[str, Any]]:
        tasks = []
        self.logger.info("Authorization proxies")
        if not self.proxies:
            raise Exception("No proxy was specified. In order to continue code execution you need to "
                            "specify a set of proxies in the format: "
                            "[{'url': proxy_url1, 'auth': proxy_auth1}, {'url': proxy_url2, 'auth': proxy_auth2}]")
        await self.proxy_auth()

        current_batch = get_next_batch(data=data, batch_size=batch_size)
        for item_data in current_batch:
            if self.user_agents:
                self.headers_settings["user-agent"] = random.choice(self.user_agents)
            proxy = random.choice(self.auth_proxies)
            tasks.append(self.fetch(item_data=item_data, proxy=proxy))
        return await asyncio.gather(*tasks)


class EbayChecker(Checker):
    def __init__(self, data: List[Dict[str, Any]], indices: Dict[str, int], proxies: list, user_agents: list,
                 shop_config: dict, exceptions: list, exceptions_repricer: list):
        super().__init__(indices=indices, proxies=proxies, user_agents=user_agents,
                         shop_config=shop_config, exceptions=exceptions, exceptions_repricer=exceptions_repricer)
        self.data: List[Dict[str, Any]] = data
        self.strategy: Literal["drop", "listings"] = shop_config.get("strategy")
        self.checked: List[Dict[str, Any]] = []

    async def _update_report(self, old_data: tuple[float, float, int], new_data: tuple[float, float, int]):
        if old_data[0] != new_data[0]:
            self.report["new_price"] += 1
        if old_data[1] != new_data[1]:
            self.report["new_ship_price"] += 1
        if old_data[2] < 1 and new_data[2] > 0:
            self.report["stock_new"] += 1
        if old_data[2] > 0 and new_data[2] < 1:
            self.report["nones_new"] += 1

    async def _parsing_triggers(self, parser: EbayParser):
        await asyncio.gather(
            parser.look_out_of_stock_triggers(),
            parser.look_pick_up_trigger(),
            parser.look_catalog_trigger(),
            parser.look_not_shipping_to_usa_trigger(self.strategy),
            parser.look_variation_trigger()
        )

    async def _parsing_main_content(self, parser: EbayParser):
        what_need_to_parse = self.shop_config.get("what_need_to_parse")
        task_map = {
            "supplier_price": parser.get_price,
            "supplier_shipping": parser.get_shipping_price,
            "supplier_qty": parser.get_quantity,
            "supplier_days": parser.get_last_shipping_day,
            "supplier_name": parser.get_supplier_name,
            "part_number": parser.get_part_number,
            "product_dimensions": parser.get_dimensions_lwh,
            "color": parser.get_color,
            "power_source": parser.get_power_source,
            "voltage": parser.get_voltage,
            "wattage": parser.get_wattage,
            "included_components": parser.get_included_components,
            "title": parser.get_item_title
        }
        tasks = [method() for key, method in task_map.items() if what_need_to_parse.get(key)]
        results = await asyncio.gather(*tasks)
        parsed_data = {}
        for key, result in zip(task_map.keys(), results):
            if what_need_to_parse.get(key):
                parsed_data[key] = result

        return parsed_data

    async def parsing_page(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        old_price = retype(item_data.get("supplier_price"), float, 0.0)
        old_shipping_price = retype(item_data.get("supplier_shipping"), float, 0.0)
        old_quantity = retype(item_data.get("supplier_qty"), int, 0)
        if item_data["variation"] == "TURE":
            return item_data

        page = item_data.pop("page")
        parser = EbayParser(page=page)

        await self._parsing_triggers(parser)

        exception_trigger = await parser.check_exceptions()
        if parser.variation:
            item_data["variation"] = "TRUE"
            return item_data
        if exception_trigger:
            item_data.update({
                "supplier_price": 0.0,
                "supplier_shipping": 0.0,
                "supplier_qty": 0,
                "supplier_name": exception_trigger
            })
            await self._update_report((old_price, old_shipping_price, old_quantity), (0.0, 0.0, 0))
            return item_data

        result = await self._parsing_main_content(parser)
        item_data.update(**result)
        return item_data

    async def start_check(self, batch_size: int = 5):
        self.logger.info("Start checking data")

        while self.data:
            items_data = await self.get_pages(self.data, batch_size=batch_size)
            for item_data in items_data:
                actual_data = await self.parsing_page(item_data)
                self.checked.append(actual_data)

    async def end_check(self):
        self.logger.info("Check was end. Cleaning cech...")
        self.checked = []
        self.proxies = None
        self.user_agents = None
        self.shop_config = None
