from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import OrderCallback
from bot.config import Settings
from bot.db.models import OrderStatus, User
from bot.formatting import format_id, order_text
from bot.notify import send_quietly, user_language
from bot.order_keyboards import admin_open_order_keyboard, customer_order_keyboard, customer_orders_keyboard
from bot.services.orders import (
    OrderNotFoundError,
    OrderStatusError,
    change_status,
    get_order,
    list_user_orders,
)
from bot.texts import t, variants

router = Router(name="orders")


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)


@router.message(F.text.in_(variants("menu.orders")))
async def my_orders(message: Message, session: AsyncSession, user: User, lang: str) -> None:
    orders = await list_user_orders(session, user.id)
    if not orders:
        await message.answer(t("orders.empty", lang))
        return
    await message.answer(t("orders.title", lang), reply_markup=customer_orders_keyboard(orders, lang))


@router.callback_query(OrderCallback.filter(F.action == "list"))
async def back_to_orders(callback: CallbackQuery, session: AsyncSession, user: User, lang: str) -> None:
    await callback.answer()
    orders = await list_user_orders(session, user.id)
    if not orders:
        await _edit(callback, t("orders.empty", lang), None)
        return
    await _edit(callback, t("orders.title", lang), customer_orders_keyboard(orders, lang))


@router.callback_query(OrderCallback.filter(F.action == "view"))
async def view_order(
    callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession, user: User, lang: str
) -> None:
    order = await get_order(session, callback_data.id)
    mine = order is not None and order.user_id == user.id
    if order is None or not mine:
        await callback.answer(t("orders.not_found", lang), show_alert=True)
        return
    await callback.answer()
    await _edit(callback, order_text(order, lang), customer_order_keyboard(order, lang))


@router.callback_query(OrderCallback.filter(F.action == "cancel"))
async def cancel_order(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    session: AsyncSession,
    user: User,
    lang: str,
    bot: Bot,
    settings: Settings,
) -> None:
    try:
        await change_status(session, callback_data.id, OrderStatus.CANCELLED, customer_id=user.id)
    except OrderNotFoundError:
        await callback.answer(t("orders.not_found", lang), show_alert=True)
        return
    except OrderStatusError:
        await callback.answer(t("orders.cannot_cancel", lang), show_alert=True)
    else:
        await callback.answer(t("orders.cancelled_by_you", lang))
        for admin_id in settings.admin_ids:
            admin_lang = await user_language(session, admin_id)
            await send_quietly(
                bot,
                admin_id,
                t("admin.order_cancelled_by_customer", admin_lang, order_id=format_id(callback_data.id, admin_lang)),
                admin_open_order_keyboard(callback_data.id, admin_lang),
            )
    order = await get_order(session, callback_data.id)
    if order is not None:
        await _edit(callback, order_text(order, lang), customer_order_keyboard(order, lang))


@router.callback_query(OrderCallback.filter())
async def other_order_button(callback: CallbackQuery) -> None:
    await callback.answer()
