import os
from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

import jdatetime

from bot.db.models import CartItem, Order, OrderStatus, Product
from bot.texts import t

# Western digits and comma -> Persian digits (U+06F0..U+06F9) and Persian thousands separator (U+066C)
_PERSIAN_DIGITS = str.maketrans(
    "0123456789,", "".join(chr(0x06F0 + i) for i in range(10)) + chr(0x066C)
)
# Dates are shown in the shop's time zone (TIMEZONE in .env)
SHOP_TIMEZONE = ZoneInfo(os.getenv("TIMEZONE") or "Asia/Tehran")


def format_number(value: int, lang: str) -> str:
    number = f"{value:,}"
    return number.translate(_PERSIAN_DIGITS) if lang == "fa" else number


def format_id(value: int, lang: str) -> str:
    """An id such as an order number: no thousands separators."""
    number = str(value)
    return number.translate(_PERSIAN_DIGITS) if lang == "fa" else number


def format_price(amount: int, lang: str) -> str:
    return t("price.format", lang, amount=format_number(amount, lang))


def format_date(moment: datetime, lang: str, with_time: bool = True) -> str:
    """Persian (Jalali) calendar and digits in Persian, Gregorian in English."""
    local = moment.astimezone(SHOP_TIMEZONE)
    pattern = "%Y/%m/%d %H:%M" if with_time else "%Y/%m/%d"
    if lang == "fa":
        return jdatetime.datetime.fromgregorian(datetime=local).strftime(pattern).translate(_PERSIAN_DIGITS)
    return local.strftime(pattern.replace("/", "-"))


def status_label(status: OrderStatus, lang: str) -> str:
    return t(f"status.{status.value}", lang)


def product_text(product: Product, lang: str) -> str:
    lines = [f"🛍 {product.name}"]
    if product.description:
        lines += ["", product.description]
    lines += ["", t("catalog.price", lang, price=format_price(product.price, lang))]
    lines.append(t("catalog.in_stock" if product.stock > 0 else "catalog.out_of_stock", lang))
    return "\n".join(lines)


def order_lines_text(lines: Sequence[tuple[str, int, int]], lang: str) -> str:
    """lines: (product name, quantity, unit price) for each row."""
    return "\n".join(
        t(
            "cart.line",
            lang,
            name=name,
            quantity=format_number(quantity, lang),
            price=format_price(price, lang),
            subtotal=format_price(quantity * price, lang),
        )
        for name, quantity, price in lines
    )


def cart_lines(items: Sequence[CartItem]) -> list[tuple[str, int, int]]:
    return [(item.product.name, item.quantity, item.product.price) for item in items]


def cart_text(items: Sequence[CartItem], lang: str) -> str:
    if not items:
        return t("cart.empty", lang)
    total = sum(quantity * price for _, quantity, price in cart_lines(items))
    return "\n".join(
        [
            t("cart.title", lang),
            "",
            order_lines_text(cart_lines(items), lang),
            "",
            t("cart.total", lang, total=format_price(total, lang)),
        ]
    )


def order_text(order: Order, lang: str) -> str:
    lines = [(item.product_name, item.quantity, item.unit_price) for item in order.items]
    return t(
        "orders.details",
        lang,
        order_id=format_id(order.id, lang),
        date=format_date(order.created_at, lang),
        status=status_label(order.status, lang),
        items=order_lines_text(lines, lang),
        total=format_price(order.total_price, lang),
        name=order.customer_name,
        phone=order.phone,
        address=order.address,
    )


def admin_product_text(
    *,
    name: str,
    category: str,
    description: str | None,
    price: int,
    stock: int,
    is_active: bool,
    lang: str,
) -> str:
    return t(
        "admin.product_details",
        lang,
        name=name,
        category=category,
        description=description or t("admin.no_description", lang),
        price=format_price(price, lang),
        stock=format_number(stock, lang),
        status=t("admin.status_visible" if is_active else "admin.status_hidden", lang),
    )
