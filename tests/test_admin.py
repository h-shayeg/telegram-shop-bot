import asyncio

from aiogram.types import User

from bot.admin_keyboards import admin_product_keyboard
from bot.config import Settings
from bot.db.models import Product
from bot.filters import IsAdmin
from bot.parsing import parse_int


def settings_with_admin(admin_id: int) -> Settings:
    return Settings(bot_token="1:x", database_url="", proxy_url=None, admin_ids=frozenset({admin_id}))


def test_parse_plain_and_separated_numbers() -> None:
    assert parse_int("120000") == 120000
    assert parse_int(" 12,500 ") == 12500


def test_parse_persian_digits_with_persian_separator() -> None:
    # "120,000" typed with Persian digits and the Persian thousands separator
    assert parse_int("\u06f1\u06f2\u06f0\u066c\u06f0\u06f0\u06f0") == 120000


def test_parse_rejects_bad_input() -> None:
    for text in ["", "abc", "-5", "1.5", "\u00b2", "1" * 13, None]:
        assert parse_int(text) is None, text


def test_is_admin_filter() -> None:
    settings = settings_with_admin(42)
    admin = User(id=42, is_bot=False, first_name="A")
    stranger = User(id=7, is_bot=False, first_name="B")
    check = IsAdmin()
    assert asyncio.run(check(None, settings=settings, event_from_user=admin)) is True
    assert asyncio.run(check(None, settings=settings, event_from_user=stranger)) is False
    assert asyncio.run(check(None, settings=settings, event_from_user=None)) is False


def test_admin_product_keyboard_toggle_label() -> None:
    visible = Product(id=1, category_id=1, name="X", price=1, stock=1, is_active=True)
    hidden = Product(id=1, category_id=1, name="X", price=1, stock=1, is_active=False)
    def toggle_text(product: Product) -> str:
        buttons = [b for row in admin_product_keyboard(product, "en").inline_keyboard for b in row]
        return next(b.text for b in buttons if b.callback_data.startswith("adm:toggle:"))

    assert toggle_text(visible) == "🚫 Hide"
    assert toggle_text(hidden) == "👁 Show"


def test_admin_callback_data_fits_telegram_limit() -> None:
    product = Product(id=10**12, category_id=10**12, name="X", price=1, stock=1, is_active=True)
    for row in admin_product_keyboard(product, "en").inline_keyboard:
        for button in row:
            assert len(button.callback_data.encode()) <= 64
