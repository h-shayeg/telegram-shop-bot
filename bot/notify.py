from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.texts import DEFAULT_LANGUAGE


async def user_language(session: AsyncSession, user_id: int) -> str:
    user = await session.get(User, user_id)
    return user.language if user else DEFAULT_LANGUAGE


async def send_quietly(
    bot: Bot, chat_id: int, text: str, markup: InlineKeyboardMarkup | None = None
) -> None:
    """Send a message, but do not fail if the person blocked the bot or never started it."""
    with suppress(TelegramAPIError):
        await bot.send_message(chat_id, text, reply_markup=markup)
