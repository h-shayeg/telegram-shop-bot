from bot.db.models import Product
from bot.texts import t

# Western digits and comma -> Persian digits (U+06F0..U+06F9) and Persian thousands separator (U+066C)
_PERSIAN_DIGITS = str.maketrans(
    "0123456789,", "".join(chr(0x06F0 + i) for i in range(10)) + "\u066c"
)


def format_number(value: int, lang: str) -> str:
    number = f"{value:,}"
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
