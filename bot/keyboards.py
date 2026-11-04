from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.callbacks import LanguageCallback
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
