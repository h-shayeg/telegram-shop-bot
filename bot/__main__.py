import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeChat

from bot.config import load_settings
from bot.db.session import make_session_factory
from bot.handlers import admin, cart, catalog, language, menu, start
from bot.middlewares.db import DbSessionMiddleware
from bot.texts import t


def bot_commands(lang: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t("commands.start", lang)),
        BotCommand(command="language", description=t("commands.language", lang)),
    ]


def admin_commands(lang: str) -> list[BotCommand]:
    return bot_commands(lang) + [
        BotCommand(command="admin", description=t("commands.admin", lang)),
        BotCommand(command="cancel", description=t("commands.cancel", lang)),
    ]


async def set_commands(bot: Bot, admin_ids: frozenset[int]) -> None:
    # Command list shown in the Telegram menu: Persian for Persian apps, English for the rest
    await bot.set_my_commands(bot_commands("en"))
    await bot.set_my_commands(bot_commands("fa"), language_code="fa")
    # Admins also see /admin and /cancel
    for admin_id in admin_ids:
        scope = BotCommandScopeChat(chat_id=admin_id)
        with suppress(TelegramBadRequest):
            await bot.set_my_commands(admin_commands("en"), scope=scope)
            await bot.set_my_commands(admin_commands("fa"), scope=scope, language_code="fa")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    session_factory = make_session_factory(settings.database_url)

    bot = Bot(token=settings.bot_token, session=AiohttpSession(proxy=settings.proxy_url))
    dp = Dispatcher(settings=settings)

    db_middleware = DbSessionMiddleware(session_factory)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)
    # The admin router goes first so an admin's form answers are not taken by other handlers
    dp.include_routers(admin.router, start.router, language.router, catalog.router, cart.router, menu.router)

    await set_commands(bot, settings.admin_ids)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
