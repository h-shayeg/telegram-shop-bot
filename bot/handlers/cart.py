from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import CartCallback
from bot.db.models import User
from bot.formatting import cart_text, format_number
from bot.keyboards import cart_keyboard
from bot.services.cart import add_to_cart, change_quantity, clear_cart, get_cart
from bot.services.catalog import get_product
from bot.texts import t, variants

router = Router(name="cart")


async def _show_cart(callback: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    items = await get_cart(session, user.id)
    if isinstance(callback.message, Message):
        # Ignore "message is not modified" when nothing changed
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(
                cart_text(items, lang), reply_markup=cart_keyboard(items, lang)
            )


@router.message(F.text.in_(variants("menu.cart")))
async def show_cart(message: Message, session: AsyncSession, user: User, lang: str) -> None:
    items = await get_cart(session, user.id)
    await message.answer(cart_text(items, lang), reply_markup=cart_keyboard(items, lang))


@router.callback_query(CartCallback.filter(F.action == "add"))
async def add_item(
    callback: CallbackQuery,
    callback_data: CartCallback,
    session: AsyncSession,
    user: User,
    lang: str,
) -> None:
    product = await get_product(session, callback_data.product_id)
    if product is None:
        await callback.answer(t("cart.unavailable", lang), show_alert=True)
        return
    added, quantity = await add_to_cart(session, user.id, product)
    if added:
        await callback.answer(t("cart.added", lang, quantity=format_number(quantity, lang)))
    else:
        await callback.answer(
            t("cart.not_enough_stock", lang, stock=format_number(product.stock, lang)),
            show_alert=True,
        )


@router.callback_query(CartCallback.filter(F.action == "view"))
async def view_cart(callback: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await callback.answer()
    await _show_cart(callback, session, user, lang)


@router.callback_query(CartCallback.filter(F.action.in_({"inc", "dec"})))
async def change_item(
    callback: CallbackQuery,
    callback_data: CartCallback,
    session: AsyncSession,
    user: User,
    lang: str,
) -> None:
    delta = 1 if callback_data.action == "inc" else -1
    changed, _ = await change_quantity(session, user.id, callback_data.product_id, delta)
    if changed or delta < 0:
        await callback.answer()
    else:
        product = await get_product(session, callback_data.product_id)
        stock = product.stock if product else 0
        await callback.answer(
            t("cart.not_enough_stock", lang, stock=format_number(stock, lang)), show_alert=True
        )
    await _show_cart(callback, session, user, lang)


@router.callback_query(CartCallback.filter(F.action == "clear"))
async def clear_items(callback: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await clear_cart(session, user.id)
    await callback.answer(t("cart.cleared", lang))
    await _show_cart(callback, session, user, lang)


@router.callback_query(CartCallback.filter(F.action == "checkout"))
async def checkout_placeholder(callback: CallbackQuery, lang: str) -> None:
    # Checkout is built in the next step
    await callback.answer(t("common.coming_soon", lang), show_alert=True)


@router.callback_query(CartCallback.filter())
async def other_cart_button(callback: CallbackQuery) -> None:
    # The product-name button in the cart only shows information
    await callback.answer()
