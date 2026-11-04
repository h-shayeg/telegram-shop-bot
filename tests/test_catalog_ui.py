import json
from pathlib import Path

from bot.db.models import Product
from bot.formatting import format_price, product_text
from bot.keyboards import product_keyboard, products_keyboard

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_products.json"


def make_product(stock: int = 5, description: str | None = "desc") -> Product:
    return Product(id=7, category_id=3, name="Mug", description=description, price=1250000, stock=stock)


def test_price_in_english_uses_commas() -> None:
    assert format_price(1250000, "en") == "1,250,000 Toman"


def test_price_in_persian_uses_persian_digits() -> None:
    # "1,250,000" written with Persian digits and the Persian thousands separator
    expected = "\u06f1\u066c\u06f2\u06f5\u06f0\u066c\u06f0\u06f0\u06f0"
    assert format_price(1250000, "fa").startswith(expected)


def test_product_text_shows_price_and_stock() -> None:
    text = product_text(make_product(), "en")
    assert "Mug" in text and "1,250,000 Toman" in text and "In stock" in text


def test_product_text_without_description() -> None:
    text = product_text(make_product(description=None), "en")
    assert "None" not in text


def test_out_of_stock_product_has_no_add_button() -> None:
    markup = product_keyboard(make_product(stock=0), "en")
    data = [button.callback_data for row in markup.inline_keyboard for button in row]
    assert "cart:add:7" not in data


def test_in_stock_product_has_add_button() -> None:
    markup = product_keyboard(make_product(stock=3), "en")
    assert markup.inline_keyboard[0][0].callback_data == "cart:add:7"


def test_products_keyboard_ends_with_back_button() -> None:
    markup = products_keyboard([make_product()], "en")
    assert markup.inline_keyboard[-1][0].callback_data == "cat:categories:0"


def test_sample_data_is_valid() -> None:
    data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
    assert data["categories"]
    for category in data["categories"]:
        assert category["name"].strip()
        for item in category["products"]:
            assert item["name"].strip()
            assert isinstance(item["price"], int) and item["price"] >= 0
            assert isinstance(item.get("stock", 0), int) and item.get("stock", 0) >= 0
