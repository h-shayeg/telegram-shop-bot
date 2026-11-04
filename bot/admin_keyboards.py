from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import AdminCallback
from bot.db.models import Category, Product
from bot.formatting import format_price
from bot.texts import t

EDITABLE_FIELDS = ("name", "description", "price", "stock")


def admin_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.add_product", lang), callback_data=AdminCallback(action="add_product"))
    builder.button(text=t("admin.products", lang), callback_data=AdminCallback(action="products"))
    builder.button(text=t("admin.add_category", lang), callback_data=AdminCallback(action="add_category"))
    builder.adjust(1)
    return builder.as_markup()


def admin_categories_keyboard(
    categories: Sequence[Category], action: str, lang: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        label = category.name if category.is_active else f"🚫 {category.name}"
        builder.button(text=label, callback_data=AdminCallback(action=action, id=category.id))
    builder.button(text=t("button.back", lang), callback_data=AdminCallback(action="menu"))
    builder.adjust(1)
    return builder.as_markup()


def admin_products_keyboard(products: Sequence[Product], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        mark = "👁" if product.is_active else "🚫"
        builder.button(
            text=f"{mark} {product.name} | {format_price(product.price, lang)}",
            callback_data=AdminCallback(action="product", id=product.id),
        )
    builder.button(text=t("button.back", lang), callback_data=AdminCallback(action="products"))
    builder.adjust(1)
    return builder.as_markup()


def admin_product_keyboard(product: Product, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for field in EDITABLE_FIELDS:
        builder.button(
            text=t(f"admin.edit_{field}", lang),
            callback_data=AdminCallback(action="edit", id=product.id, field=field),
        )
    builder.button(
        text=t("admin.hide" if product.is_active else "admin.show", lang),
        callback_data=AdminCallback(action="toggle", id=product.id),
    )
    builder.button(
        text=t("button.back", lang),
        callback_data=AdminCallback(action="category", id=product.category_id),
    )
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin.save", lang), callback_data=AdminCallback(action="save"))
    builder.button(text=t("admin.cancel_button", lang), callback_data=AdminCallback(action="cancel"))
    builder.adjust(2)
    return builder.as_markup()
