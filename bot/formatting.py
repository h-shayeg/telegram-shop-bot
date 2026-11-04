from bot.db.models import Product
from bot.texts import t

# Western digits and comma -> Persian digits (U+06F0..U+06F9) and Persian thousands separator (U+066C)
_PERSIAN_DIGITS = str.maketrans(
    "0123456789,", "".join(chr(0x06F0 + i) for i in range(10)) + "\u066c"
)


def format_price(amount: int, lang: str) -> str:
    number = f"{amount:,}"
    if lang == "fa":
        number = number.translate(_PERSIAN_DIGITS)
    return t("price.format", lang, amount=number)


def product_text(product: Product, lang: str) -> str:
    lines = [f"🛍 {product.name}"]
    if product.description:
        lines += ["", product.description]
    lines += ["", t("catalog.price", lang, price=format_price(product.price, lang))]
    lines.append(t("catalog.in_stock" if product.stock > 0 else "catalog.out_of_stock", lang))
    return "\n".join(lines)
