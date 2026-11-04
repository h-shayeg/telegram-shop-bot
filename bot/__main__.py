import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand

from bot.config import load_settings
from bot.db.session import make_session_factory
from bot.handlers import catalog, language, menu, start
from bot.middlewares.db import DbSessionMiddleware
from bot.texts import t


def bot_commands(lang: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t("commands.start", lang)),
        BotCommand(command="language", description=t("commands.language", lang)),
    ]


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    session_factory = make_session_factory(settings.database_url)

    bot = Bot(token=settings.bot_token, session=AiohttpSession(proxy=settings.proxy_url))
    dp = Dispatcher()

    db_middleware = DbSessionMiddleware(session_factory)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)
    dp.include_routers(start.router, language.router, catalog.router, menu.router)

    # Command list shown in the Telegram menu: Persian for Persian apps, English for the rest
    await bot.set_my_commands(bot_commands("en"))
    await bot.set_my_commands(bot_commands("fa"), language_code="fa")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
