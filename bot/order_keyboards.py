from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import AdminCallback, AdminOrderCallback, OrderCallback
from bot.db.models import Order, OrderStatus
from bot.formatting import format_date, format_id, format_price, status_label
from bot.services.orders import ALLOWED_TRANSITIONS
from bot.texts import t


def customer_orders_keyboard(orders: Sequence[Order], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=(
                f"#{format_id(order.id, lang)} | {format_date(order.created_at, lang, with_time=False)}"
                f" | {status_label(order.status, lang)}"
            ),
            callback_data=OrderCallback(action="view", id=order.id),
        )
    builder.adjust(1)
    return builder.as_markup()


def customer_order_keyboard(order: Order, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if order.status == OrderStatus.NEW:
        builder.button(text=t("orders.cancel", lang), callback_data=OrderCallback(action="cancel", id=order.id))
    builder.button(text=t("button.back", lang), callback_data=OrderCallback(action="list"))
    builder.adjust(1)
    return builder.as_markup()


def view_order_keyboard(order_id: int, lang: str) -> InlineKeyboardMarkup:
    """Single button under a status-change message sent to the customer."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("orders.view", lang), callback_data=OrderCallback(action="view", id=order_id))
    return builder.as_markup()


def admin_orders_keyboard(orders: Sequence[Order], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=(
                f"#{format_id(order.id, lang)} | {status_label(order.status, lang)}"
                f" | {format_price(order.total_price, lang)}"
            ),
            callback_data=AdminOrderCallback(action="view", id=order.id),
        )
    builder.button(text=t("button.back", lang), callback_data=AdminCallback(action="menu"))
    builder.adjust(1)
    return builder.as_markup()


def admin_order_keyboard(order: Order, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status in ALLOWED_TRANSITIONS[order.status]:
        builder.button(
            text=t("admin.set_status", lang, status=status_label(status, lang)),
            callback_data=AdminOrderCallback(action="set", id=order.id, status=status.value),
        )
    builder.button(text=t("button.back", lang), callback_data=AdminOrderCallback(action="list"))
    builder.adjust(1)
    return builder.as_markup()


def admin_open_order_keyboard(order_id: int, lang: str) -> InlineKeyboardMarkup:
    """Single button under the "new order" message sent to admins."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("orders.view", lang), callback_data=AdminOrderCallback(action="view", id=order_id))
    return builder.as_markup()
