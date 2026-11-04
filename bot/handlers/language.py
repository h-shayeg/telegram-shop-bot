from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import LanguageCallback
from bot.db.models import User
from bot.keyboards import language_keyboard, main_menu
from bot.texts import SUPPORTED_LANGUAGES, t, variants

router = Router(name="language")


@router.message(Command("language"))
@router.message(F.text.in_(variants("menu.language")))
async def choose_language(message: Message, lang: str) -> None:
    await message.answer(t("language.choose", lang), reply_markup=language_keyboard())


@router.callback_query(LanguageCallback.filter())
async def set_language(
    callback: CallbackQuery,
    callback_data: LanguageCallback,
    session: AsyncSession,
    user: User,
) -> None:
    await callback.answer()
    if callback_data.code not in SUPPORTED_LANGUAGES:
        return
    user.language = callback_data.code
    await session.commit()
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.delete()
        await callback.message.answer(
            t("language.changed", user.language), reply_markup=main_menu(user.language)
        )
