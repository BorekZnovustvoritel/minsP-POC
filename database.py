from dataclasses import dataclass
from functools import lru_cache
from datetime import date
from json import loads

from aiohttp import ClientSession
from sqlalchemy import (
    Integer,
    String,
    Float,
    Boolean,
    LargeBinary,
    DateTime,
    BigInteger,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column

from definitions import _


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "product"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(50), nullable=False)
    description = mapped_column(String(1024))
    price_czk = mapped_column(Float, nullable=False)
    image_id = mapped_column(Integer)
    in_stock = mapped_column(Integer, nullable=False, default=1)

    @lru_cache
    async def get_price_eur(self, _: date) -> float:
        async with ClientSession() as session:
            async with session.get("https://data.kurzy.cz/json/meny/b[1].json") as resp:
                ans = loads(await resp.text())
                return self.price_czk / ans["kurzy"]["EUR"]["dev_nakup"]

    async def translate(self, lang: str, quantity: int = 1) -> "TranslatedProduct":
        price = self.price_czk
        if lang != "cs_CZ":
            price = await self.get_price_eur(date.today())
        price_str = _("€{price:.2f}", lang).format(price=price)
        return TranslatedProduct(
            id=self.id,
            name=_(self.name, lang),
            image_id=self.image_id,
            price_str=price_str,
            description=_(self.description, lang),
            quantity=quantity,
        )


@dataclass
class TranslatedProduct:
    id: int
    name: str
    description: str
    price_str: str
    image_id: int
    quantity: int


class Image(Base):
    __tablename__ = "image"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(256), nullable=False)
    data = mapped_column(LargeBinary)


class Reservation(Base):
    __tablename__ = "reservation"
    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(DateTime)
    user_id = mapped_column(BigInteger)
    product_id = mapped_column(Integer)
    quantity = mapped_column(Integer)


class Order(Base):
    __tablename__ = "order_table"

    id = mapped_column(Integer, primary_key=True)
    outstanding = mapped_column(Boolean, default=True)
    paid = mapped_column(Boolean, default=False)
    user_id = mapped_column(BigInteger)
    reservation_id = mapped_column(Integer)
    first_name = mapped_column(String)
    last_name = mapped_column(String)
    email = mapped_column(String)
    phone = mapped_column(String)
    country = mapped_column(String)
    postal_code = mapped_column(String)
    city = mapped_column(String)
    address_line_1 = mapped_column(String)
    address_line_2 = mapped_column(String)


class OrderedItem(Base):
    __tablename__ = "ordered_item"
    id = mapped_column(Integer, primary_key=True)
    order_id = mapped_column(Integer)
    item_id = mapped_column(Integer)
    quantity = mapped_column(Integer)
