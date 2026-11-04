from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin_keyboards import admin_menu_keyboard
from bot.callbacks import AdminOrderCallback
from bot.db.models import OrderStatus
from bot.filters import IsAdmin
from bot.formatting import format_id, order_text, status_label
from bot.notify import send_quietly, user_language
from bot.order_keyboards import admin_order_keyboard, admin_orders_keyboard, view_order_keyboard
from bot.services.orders import (
    OrderNotFoundError,
    OrderStatusError,
    change_status,
    get_order,
    list_open_orders,
)
from bot.texts import t

router = Router(name="admin_orders")
router.callback_query.filter(IsAdmin())


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(AdminOrderCallback.filter(F.action == "list"))
async def open_orders(callback: CallbackQuery, session: AsyncSession, lang: str) -> None:
    await callback.answer()
    orders = await list_open_orders(session)
    if not orders:
        await _edit(callback, t("admin.no_open_orders", lang), admin_menu_keyboard(lang))
        return
    await _edit(callback, t("admin.open_orders", lang), admin_orders_keyboard(orders, lang))


@router.callback_query(AdminOrderCallback.filter(F.action == "view"))
async def view_order(
    callback: CallbackQuery, callback_data: AdminOrderCallback, session: AsyncSession, lang: str
) -> None:
    order = await get_order(session, callback_data.id)
    if order is None:
        await callback.answer(t("orders.not_found", lang), show_alert=True)
        return
    await callback.answer()
    await _edit(callback, order_text(order, lang), admin_order_keyboard(order, lang))


@router.callback_query(AdminOrderCallback.filter(F.action == "set"))
async def set_status(
    callback: CallbackQuery,
    callback_data: AdminOrderCallback,
    session: AsyncSession,
    lang: str,
    bot: Bot,
) -> None:
    try:
        new_status = OrderStatus(callback_data.status)
        order = await change_status(session, callback_data.id, new_status)
    except (ValueError, OrderNotFoundError):
        await callback.answer(t("orders.not_found", lang), show_alert=True)
        return
    except OrderStatusError:
        await callback.answer(t("admin.invalid_transition", lang), show_alert=True)
        order = await get_order(session, callback_data.id)
        if order is not None:
            await _edit(callback, order_text(order, lang), admin_order_keyboard(order, lang))
        return
    await callback.answer(t("admin.status_updated", lang))
    order = await get_order(session, callback_data.id)
    if order is None:
        return
    await _edit(callback, order_text(order, lang), admin_order_keyboard(order, lang))
    # Tell the customer, in the customer's own language
    customer_lang = await user_language(session, order.user_id)
    await send_quietly(
        bot,
        order.user_id,
        t(
            "orders.status_changed",
            customer_lang,
            order_id=format_id(order.id, customer_lang),
            status=status_label(order.status, customer_lang),
        ),
        view_order_keyboard(order.id, customer_lang),
    )


@router.callback_query(AdminOrderCallback.filter())
async def other_admin_order_button(callback: CallbackQuery) -> None:
    await callback.answer()
