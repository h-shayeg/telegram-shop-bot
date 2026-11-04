from collections.abc import Sequence

from bot.db.models import CartItem, Product
from bot.texts import t

# Western digits and comma -> Persian digits (U+06F0..U+06F9) and Persian thousands separator (U+066C)
_PERSIAN_DIGITS = str.maketrans(
    "0123456789,", "".join(chr(0x06F0 + i) for i in range(10)) + chr(0x066C)
)


def format_number(value: int, lang: str) -> str:
    number = f"{value:,}"
    return number.translate(_PERSIAN_DIGITS) if lang == "fa" else number


def format_id(value: int, lang: str) -> str:
    """An id such as an order number: no thousands separators."""
    number = str(value)
    return number.translate(_PERSIAN_DIGITS) if lang == "fa" else number


def format_price(amount: int, lang: str) -> str:
    return t("price.format", lang, amount=format_number(amount, lang))


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
