from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import CartCallback, CatalogCallback
from bot.formatting import product_text
from bot.keyboards import categories_keyboard, product_keyboard, products_keyboard
from bot.services.catalog import get_category, get_product, list_categories, list_products
from bot.texts import t, variants

router = Router(name="catalog")


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    if isinstance(callback.message, Message):
        # Ignore "message is not modified" when the same button is tapped twice
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)


@router.message(F.text.in_(variants("menu.products")))
async def show_categories(message: Message, session: AsyncSession, lang: str) -> None:
    categories = await list_categories(session)
    if not categories:
        await message.answer(t("catalog.empty", lang))
        return
    await message.answer(
        t("catalog.choose_category", lang), reply_markup=categories_keyboard(categories)
    )


@router.callback_query(CatalogCallback.filter(F.action == "categories"))
async def back_to_categories(callback: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await callback.answer()
    categories = await list_categories(session)
    if not categories:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(t("catalog.empty", lang))
        return
    await _edit(callback, t("catalog.choose_category", lang), categories_keyboard(categories))


@router.callback_query(CatalogCallback.filter(F.action == "category"))
async def show_category(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    session: AsyncSession,
    lang: str,
) -> None:
    category = await get_category(session, callback_data.id)
    if category is None:
        await callback.answer(t("catalog.empty_category", lang), show_alert=True)
        return
    await callback.answer()
    products = await list_products(session, category.id)
    text = (
        t("catalog.choose_product", lang, category=category.name)
        if products
        else t("catalog.empty_category", lang)
    )
    await _edit(callback, text, products_keyboard(products, lang))


@router.callback_query(CatalogCallback.filter(F.action == "product"))
async def show_product(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    session: AsyncSession,
    lang: str,
) -> None:
    product = await get_product(session, callback_data.id)
    if product is None:
        await callback.answer(t("catalog.not_found", lang), show_alert=True)
        return
    await callback.answer()
    await _edit(callback, product_text(product, lang), product_keyboard(product, lang))


@router.callback_query(CartCallback.filter(F.action == "add"))
async def add_to_cart_placeholder(callback: CallbackQuery, lang: str) -> None:
    # The cart is built in the next step
    await callback.answer(t("common.coming_soon", lang), show_alert=True)
