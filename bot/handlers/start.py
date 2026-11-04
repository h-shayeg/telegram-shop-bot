from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.db.models import User
from bot.keyboards import main_menu
from bot.texts import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, lang: str) -> None:
    await message.answer(
        t("start.welcome", lang, name=user.first_name), reply_markup=main_menu(lang)
    )
