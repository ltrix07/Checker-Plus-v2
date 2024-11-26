import logging
import re
from typing import Literal
from checker_plus.utils import date_to_days


class Parser:
    """
    Родительский клаас для парсинга страниц товаров.
    :param page: Страница сайта в формате str.
    """
    def __init__(self, page: str):
        self.page = page

    async def search(self, patterns: list, in_text=False) -> str | True | None:
        """
        Ищет паттерны внутри страницы при помощи регулярных выражений. Приоритетность от первого паттерна в списке
        до последнего. Если паттерна нет на странице, то ищет следующий.
        :param patterns: Список из регулярных вырежаений.
        :param in_text: Булевое значение если нужно просто проверить находится ли паттерн на странице, но не надо
        возвращать текст.
        :return: str - когда паттерн найден; True - наличие паттерна на странице; None - паттерн на странице не найден.
        """
        for pattern in patterns:
            match = re.search(pattern, self.page, re.IGNORECASE | re.DOTALL)
            if match and not in_text:
                return match.group(1)
            elif match and in_text:
                return True


class EbayParser(Parser):
    """
    Класс для парсинга eBay страницы. Наследует класс 'Parser'.
    :param page: Страница сайта в формате str.
    """
    OUT_OFF_STOCK_TRIGGERS = [
        r'CURRENTLY SOLD OUT', r'We looked everywhere.', r'Looks like this page is missing.',
        r'The item you selected is unavailable', r'The item you selected has ended',
        r'This listing was ended', r'The listing you\'re looking for has ended',
        r'Service Unavailable - Zero size object', r'This item is out of stock.',
        r'This listing sold', r'This listing ended'
    ]
    VARIATION_TRIGGERS = [
        r'<option value=-1'
    ]
    CATALOG_TRIGGERS = [
        r'class=\"cat-wrapper\"',
        r'class=\"s-item s-item__pl-on-bottom\"'
    ]
    NOT_SHIP_TO_USA_TRIGGERS = [
        r'does not ship to (.*?)</span>'
    ]
    OTHER_COUNTRIES_TRIGGERS = [
        r'located in: .*?(usa|us|united states)\\b.*?</span>'
    ]
    PICK_UP_TRIGGERS = [
        r'Local pickup only'
    ]

    SUPPLIER_PRICE = [
        r'"price":"([0-9]+\.[0-9]+)"'
    ]
    SUPPLIER_SHIPPING = [
        r'"shippingRate":.*"value":"([0-9]+\.[0-9]+)"'
    ]
    SUPPLIER_QTY = [
        r'"maxValue":"([0-9]+)"'
    ]
    SUPPLIER_LAST_DELIVERY_DAY = [
        r'and "},{"_type":"TextSpan","text":"(.*?)"',
        r'Get it by\\s+(.*?)<',
        r'Estimated on or before\\s+(.*?)<'
    ]
    SUPPLIER_NAME = [
        r'class="vim x-sellercard-atf".*?"_ssn":"(.*?)",',
        r'<div class=x-sellercard-atf__info__about-seller title="(.*?)">',
        r'<div class=x-sellercard-atf__info__about-seller title=(.*?)>'
    ]
    PART_NUMBER = [
        r'<span class=ux-textspans>MPN.*?<span class=ux-textspans>(.*?)</span>',
        r'<span class=ux-textspans>Manufacturer Part Number.*?<span class=ux-textspans>(.*?)</span>'
    ]
    POWER_SOURCE = [
        r'<span class=ux-textspans>Power Source.*?<span class=ux-textspans>(.*?)</span>'
    ]
    VOLTAGE = [
        r'<span class=ux-textspans>Voltage.*?<span class=ux-textspans>(.*?)</span>'
    ]
    WATTAGE = [
        r'<span class=ux-textspans>Wattage.*?<span class=ux-textspans>(.*?)</span>'
    ]
    INCLUDE_COMPONENTS = [
        r'<span class=ux-textspans>Battery Included.*?<span class=ux-textspans>(.*?)</span>'
    ]
    TITLE = [
        r'<title>(.*?)</title>'
    ]
    COLOR = [
        r'<span class=ux-textspans>Color.*?<span class=ux-textspans>(.*?)</span>'
    ]
    LENGTH = [
        r'<span class=ux-textspans>Item Length.*?<span class=ux-textspans>(.*?)</span>'
    ]
    WIDTH = [
        r'<span class=ux-textspans>Item Width.*?<span class=ux-textspans>(.*?)</span>'
    ]
    HEIGHT = [
        r'<span class=ux-textspans>Item Height.*?<span class=ux-textspans>(.*?)</span>'
    ]

    def __init__(self, page: str):
        super().__init__(page=page)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.out_of_stock: bool = False
        self.variation: bool = False
        self.catalog_link: bool = False
        self.proxy_ban: bool = False
        self.not_send_to_usa: bool = False
        self.pick_up: bool = False

    async def check_exceptions(self):
        """
        Проверяет исключения на странице. :return: Tuple - исключение [Статус исключения, Информационная строка для
        занесения в файл с ошибками]; None - исключений не найдено.
        """
        if self.out_of_stock:
            return "{out_of_stock}", None
        if self.catalog_link:
            return "{link_on_catalog}", "Ссылка на каталог товаров, а не на карточку товара."
        if self.proxy_ban:
            return "{proxy_ban}"
        if self.not_send_to_usa:
            return "{supplier_not_in_usa}", "Поставщик не в США."
        if self.pick_up:
            return "{pick_up_only}", "У поставщика только самовывоз."

    async def look_out_of_stock_triggers(self) -> None:
        """
        Проверяет 'out of stock' триггеры. Т.е. те, при которых нужно всегда ставить кол-во 0.
        :return: Меняет 'self.out_of_stock' на значение True.
        """
        trigger = await self.search(self.OUT_OFF_STOCK_TRIGGERS, in_text=True)
        if trigger:
            self.out_of_stock = True

    async def look_variation_trigger(self) -> None:
        """
        Товар вариация или нет.
        :return: Меняет 'self.variation' на значение True.
        """
        trigger = await self.search(self.VARIATION_TRIGGERS, in_text=True)
        if trigger:
            self.variation = True

    async def look_catalog_trigger(self) -> None:
        """
        Ссылка на каталог или нет.
        :return: Меняет 'self.catalog_link' на значение True.
        """
        trigger = await self.search(self.CATALOG_TRIGGERS, in_text=True)
        if trigger:
            self.catalog_link = True

    async def look_not_shipping_to_usa_trigger(self, strategy: Literal["drop", "listings"]) -> None:
        """
        Проверяет работоспособность прокси, а так же ошибку когда поставщик не доставляет товар в США.
        :param strategy: Стратегия магазина. Может принимать значения: drop, listings.
        :return: Меняет значения переменных 'self.proxy_ban' и 'self.not_send_to_usa' на True в случае
        отработки триггера.
        """
        trigger = await self.search(self.NOT_SHIP_TO_USA_TRIGGERS)
        if trigger:
            lower_trigger = trigger.lower()
            if "united states" not in lower_trigger and "usa" not in lower_trigger:
                self.proxy_ban = True  # сайт думает, что мы не в США.
            elif strategy == "drop" and ("united states" in lower_trigger or "usa" in lower_trigger):
                self.not_send_to_usa = True  # поставщик не отправляет в США.

    async def look_pick_up_trigger(self) -> None:
        trigger = await self.search(self.PICK_UP_TRIGGERS, in_text=True)
        if trigger:
            self.pick_up = True

    async def get_item_title(self) -> str | None:
        title = await self.search(self.TITLE)
        if "| eBay" in title:
            return title.replace("&apos;", "'") \
                .replace("&quot;", "\"") \
                .replace("&amp;", "&") \
                .replace("&lt;", "<") \
                .replace("&gt;", ">") \
                .replace("| eBay", "") \
                .strip()
        return None

    async def get_price(self) -> str | None:
        return await self.search(self.SUPPLIER_PRICE)

    async def get_shipping_price(self) -> str | None:
        return await self.search(self.SUPPLIER_SHIPPING)

    async def get_quantity(self) -> str | None:
        return await self.search(self.SUPPLIER_QTY)

    async def get_last_shipping_day(self) -> str | None:
        last_date = await self.search(self.SUPPLIER_LAST_DELIVERY_DAY)
        return await date_to_days(last_date)

    async def get_supplier_name(self) -> str | None:
        return await self.search(self.SUPPLIER_NAME)

    async def get_part_number(self) -> str | None:
        return await self.search(self.PART_NUMBER)

    async def get_color(self) -> str | None:
        return await self.search(self.COLOR)

    async def get_power_source(self) -> str | None:
        return await self.search(self.POWER_SOURCE)

    async def get_voltage(self) -> str | None:
        return await self.search(self.VOLTAGE)

    async def get_wattage(self) -> str | None:
        return await self.search(self.WATTAGE)

    async def get_included_components(self) -> str | None:
        return await self.search(self.INCLUDE_COMPONENTS)

    async def get_length(self) -> str | None:
        return await self.search(self.LENGTH)

    async def get_width(self) -> str | None:
        return await self.search(self.WIDTH)

    async def get_height(self) -> str | None:
        return await self.search(self.HEIGHT)

    async def get_dimensions_lwh(self) -> str | None:
        length = await self.get_length()
        width = await self.get_width()
        height = await self.get_height()
        if not length:
            self.logger.warning("Length is None.")
        if not width:
            self.logger.warning("Width is None.")
        if not height:
            self.logger.warning("Height is None.")

        if length and width and height:
            return f"{length} x {width} x {height}"
        else:
            return None
