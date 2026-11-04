from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.callbacks import CartCallback, CatalogCallback, LanguageCallback
from bot.db.models import Category, Product
from bot.formatting import format_price
from bot.texts import SUPPORTED_LANGUAGES, t


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for key in ("menu.products", "menu.cart", "menu.orders", "menu.language"):
        builder.button(text=t(key, lang))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in SUPPORTED_LANGUAGES:
        builder.button(text=t("language.name", code), callback_data=LanguageCallback(code=code))
    builder.adjust(2)
    return builder.as_markup()


def categories_keyboard(categories: Sequence[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name, callback_data=CatalogCallback(action="category", id=category.id)
        )
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: Sequence[Product], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product.name} | {format_price(product.price, lang)}",
            callback_data=CatalogCallback(action="product", id=product.id),
        )
    builder.button(text=t("button.back", lang), callback_data=CatalogCallback(action="categories"))
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(product: Product, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if product.stock > 0:
        builder.button(
            text=t("button.add_to_cart", lang),
            callback_data=CartCallback(action="add", product_id=product.id),
        )
    builder.button(
        text=t("button.back", lang),
        callback_data=CatalogCallback(action="category", id=product.category_id),
    )
    builder.adjust(1)
    return builder.as_markup()
