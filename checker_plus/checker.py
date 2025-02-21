import logging
import random
import aiohttp
import asyncio
from checker_plus.cache_handler import CSV
from checker_plus.utils import read_json, get_next_batch, retype
from checker_plus.parser import EbayParser
from typing import List, Dict, Literal, Any
from aiohttp import BasicAuth
from aiohttp import client_exceptions
from pathlib import Path


class Checker:
    """
    Общий класс чекера, который описывают логику работы пакета для сбора информации из ссылок поставщиков,
    полученных из таблицы инвентаря.

    Этот класс является родительским для всех остальных в этом пакете.
    :param proxies: Список прокси.
    :param user_agents: Список юзер агентов.
    :param shop_config: Параметры магазина. Обычно должны быть получены из файла shop_data.json
    :param exceptions: Список СКУ тех товаров, на которых не нужно обновлять информацию даже если есть новые данные.
    :param exceptions_repricer: Список СКУ тех товаров, которые не надо обновлять в Репрайсере.
    """
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
                "request_errors": 0,
                "proxy_errors": 0,
                "time_out_errors": 0,
                "server_close_connection": 0,
                "site_close_connection": 0,
                "website_close_connection": 0,
                "400": 0,
                "404": 0
            },
        }

        self.headers_settings = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        self.auth_proxies: List[dict] = []

    def __call__(self, *args, **kwargs):
        """
        При определении класса проверяем есть ли файл headers_settings.json.
        Если файл есть, то читаем с него стандартные настройки заголовков.
        """
        try:
            self.headers_settings.update(read_json(self.CURRENT_DIR.parent / "db" / "#general" / "headers_settings.json"))
        except FileNotFoundError:
            pass

    async def proxy_auth(self) -> None:
        """
        Производит авторизацию прокси при помощи 'aiohttp.BasicAuth' для дальнейшего их использования через 'aiohttp'.
        :return: None
        """
        for proxy in self.proxies:
            if "@" not in proxy or ":" not in proxy:
                raise TypeError(f"Your proxy must be type 'login:password@ip:port' you specified '{proxy}'")
            username = proxy.split(':')[0]
            password = proxy.split(':')[1].split('@')[0]
            host_and_port = proxy.split('@')[1]

            proxy_url = 'http://' + host_and_port
            proxy_auth = BasicAuth(username, password)

            self.auth_proxies.append({"url": proxy_url, "auth": proxy_auth})

    async def request(self, link: str, proxy: dict) -> str | None:
        """
        Производит запрос по ссылке для получения контекста страницы.
        :param link: Ссылка на товар.
        :param proxy: Прокси авторизованный через 'aiohttp.BasicAuth'.
        :return: Наполнение страницы в виде строки либо словарь с ошибкой.
        """
        timeout = aiohttp.ClientTimeout(total=30)
        proxy_url = proxy.get("url") if proxy else None
        proxy_auth = proxy.get("auth") if proxy else None

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(
                        link, proxy=proxy_url, proxy_auth=proxy_auth, headers=self.headers_settings
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        self.logger.warning(f"403 Forbidden: Link={link}, Proxy={proxy}")
                        self.report["errors"]["403"] += 1
                        return f"403 Forbidden: {link}"
                    elif response.status == 404:
                        self.report["errors"]["404"] += 1
                        return f"404 Not Found: {link}"
                    elif 500 <= response.status < 600:
                        self.logger.warning(f"Server error {response.status} for URL: {link}")
                        self.report["errors"]["server_errors"] += 1
                        return f"Server error {response.status}: {link}"
                    else:
                        self.logger.error(f"Unexpected status {response.status} for URL: {link}")
                        self.report["errors"]["unknown"] += 1
                        return f"Unknown status {response.status}: {link}"
            except (TimeoutError, client_exceptions.ClientProxyConnectionError, client_exceptions.ClientConnectorError,
                    client_exceptions.ClientOSError) as e:
                self.logger.error(f"Request error: {e}, Link={link}")
                self.report["errors"]["request_errors"] += 1
                return f"Request error: {str(e)}"
            except Exception as e:
                self.logger.error(f"Unhandled error: {e}, Link={link}")
                self.report["errors"]["unknown"] += 1
                return f"Unhandled error: {str(e)}"

    async def fetch(self, item_data: Dict[str, Any], proxy: dict) -> dict:
        """
        Функция для подготовки данных к запросу через метод 'Checker.request'
        :param item_data: Словарь в виде данных полученных по определенному товару из таблицы
        :param proxy: Прокси авторизованный через 'aiohttp.BasicAuth'.
        :return: Словарь в формате 'item_data' но с дополнительной информацией в ключе 'page'.
        """
        sku = item_data.get("sku")
        link = item_data.get("supplier_link")
        if sku in self.exceptions or sku == '' or not sku or link == '' or not link:
            item_data["page"] = None
            return item_data

        item_data["page"] = await self.request(link, proxy)
        
        return item_data

    async def get_pages(self, data: List[Dict[str, Any]], batch_size: int = 5) -> tuple[Dict[str, Any]]:
        """
        Порционно проходит по списку данных, полученных из таблиц, и получает контекст страниц по полученным ссылкам.
        :param data: Список с вложенными словарями. Каждый вложенный словарь - это строка из таблицы ключем, которого
        является название колонки, а значение - соответствующее значение в этой колонке.
        :param batch_size: Размер порции. По умолчанию 5.
        :return: tuple[Dict[str, Any]]
        """
        tasks = []
        all_data_len = len(data)
        checked = batch_size
        self.logger.info("Authorization proxies")
        if not self.proxies:
            raise Exception("No proxy was specified. In order to continue code execution you need to "
                            "specify a set of proxies in the format: "
                            "[{'url': proxy_url1, 'auth': proxy_auth1}, {'url': proxy_url2, 'auth': proxy_auth2}]")
        await self.proxy_auth()

        self.logger.info(f"Checking: [{checked} | {all_data_len}]")
        current_batch = get_next_batch(data=data, batch_size=batch_size)
        for item_data in current_batch:
            if self.user_agents:
                self.headers_settings["user-agent"] = random.choice(self.user_agents)
            proxy = random.choice(self.auth_proxies)
            tasks.append(self.fetch(item_data=item_data, proxy=proxy))
            checked += batch_size
        return await asyncio.gather(*tasks)


class EbayChecker(Checker):
    """
    Класс нацеленный на обработку товаров с ebay.com. Он наследует класс Checker.
    :param data: Список с вложенными словарями. Каждый вложенный словарь - это строка из таблицы ключем, которого
        является название колонки, а значение - соответствующее значение в этой колонке.

    Остальные параметры имеют аналогичное значение, как и в родительском классе Checker.
    """
    def __init__(self, data: List[Dict[str, Any]], proxies: list, user_agents: list,
                 shop_config: dict, exceptions: list, exceptions_repricer: list, cache_path: CSV, errors_path: CSV):
        super().__init__(proxies=proxies, user_agents=user_agents,
                         shop_config=shop_config, exceptions=exceptions, exceptions_repricer=exceptions_repricer)
        self.data: List[Dict[str, Any]] = data
        self.strategy: Literal["drop", "listings"] = shop_config.get("strategy")
        self.cache_file = cache_path
        self.errors_file = errors_path

    async def _update_report(self, old_data: tuple[float, float, int], new_data: tuple[float, float, int]):
        """
        Обновляет объект отчета по путем сравнения старой информации из таблицы и новой, полученной из ссылки.
        :param old_data: Кортеж из трех старых значений (цена, цена доставки, количество)
        :param new_data: Кортеж из трех новых значений
        :return: None
        """
        if old_data[0] != new_data[0]:
            self.report["new_price"] += 1
        if old_data[1] != new_data[1]:
            self.report["new_ship_price"] += 1
        if old_data[2] < 1 and new_data[2] > 0:
            self.report["stock_new"] += 1
        if old_data[2] > 0 and new_data[2] < 1:
            self.report["nones_new"] += 1

    async def _parsing_triggers(self, parser: EbayParser):
        """
        Проверяет триггерные места на странице. Те, что указывают на отсутствие товара неверное местоположение и т.д.
        :param parser: Экземпляр класса EbayParser
        :return: None
        """
        await asyncio.gather(
            parser.look_out_of_stock_triggers(),
            parser.look_pick_up_trigger(),
            parser.look_catalog_trigger(),
            parser.look_not_shipping_to_usa_trigger(self.strategy),
            parser.look_variation_trigger()
        )

    async def _parsing_main_content(self, parser: EbayParser):
        """
        Собирает основной контент со страницы. Для определения того что нужно собрать, а что нет использует значение
        'what_need_to_parse' из объекта конфигурации.
        :param parser: Экземпляр класса EbayParser
        :return: Словарь с собранными данными.
        """
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
        """
        На основе информации в словаре 'item_data' что является элементом списка с данными из таблицы,
        собирает данные со страницы.
        :param item_data: Объект строки с данными, в которой уже есть ключ 'page'.
        :return: Объект 'item_data' с новой информацией полученной со страницы.
        """
        page = item_data.pop("page")
        if not page:
            item_data.update({
                "supplier_price": 0.0,
                "supplier_shipping": 0.0,
                "supplier_qty": 0,
                "supplier_name": '{no_page}'
            })
            return item_data

        old_price = retype(item_data.get("supplier_price"), float, 0.0)
        old_shipping_price = retype(item_data.get("supplier_shipping"), float, 0.0)
        old_quantity = retype(item_data.get("supplier_qty"), int, 0)
        if item_data["variation"] == "TURE":
            return item_data

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
                "supplier_name": exception_trigger[0]
            })
            if exception_trigger[1]:
                self.errors_file.append_to_file([{"sku": item_data["sku"], "error_type": exception_trigger[1]}],
                                                ["sku", "error_type"])
            await self._update_report((old_price, old_shipping_price, old_quantity), (0.0, 0.0, 0))
            return item_data

        result = await self._parsing_main_content(parser)
        item_data.update(**result)
        return item_data

    async def start_check(self, batch_size: int = 5):
        """
        Начинает работу чекера.
        :param batch_size: Размер шага для порционного чека ссылок. По умолчанию 5.
        :return: None
        """
        self.logger.info("Start checking data")

        while self.data:
            items_data = await self.get_pages(self.data, batch_size=batch_size)
            new_data = []
            for item_data in items_data:
                actual_data = await self.parsing_page(item_data)
                new_data.append(actual_data)
            self.cache_file.append_to_file(new_data, self.shop_config.get("columns"))

    async def end_check(self):
        """
        Заканчивает работу чекера и очищает кеш.
        :return: None
        """
        self.logger.info("Check was end. Cleaning cech...")
        self.proxies = None
        self.user_agents = None
        self.shop_config = None
