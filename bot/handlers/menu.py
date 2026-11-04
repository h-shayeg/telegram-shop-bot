from aiogram import F, Router
from aiogram.types import Message

from bot.texts import t, variants

router = Router(name="menu")

# Sections that are not built yet
COMING_SOON = variants("menu.cart") | variants("menu.orders")


@router.message(F.text.in_(COMING_SOON))
async def coming_soon(message: Message, lang: str) -> None:
    await message.answer(t("common.coming_soon", lang))
