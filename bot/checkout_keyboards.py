from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.callbacks import CheckoutCallback
from bot.texts import t


def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("checkout.cancel_button", lang))
    return builder.as_markup(resize_keyboard=True)


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("checkout.share_phone", lang), request_contact=True)
    builder.button(text=t("checkout.cancel_button", lang))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def confirm_order_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("checkout.confirm", lang), callback_data=CheckoutCallback(action="confirm"))
    builder.button(text=t("checkout.cancel_button", lang), callback_data=CheckoutCallback(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()
