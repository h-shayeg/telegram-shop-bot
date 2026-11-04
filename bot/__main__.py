import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from bot.config import load_settings
from bot.handlers import start


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    session = AiohttpSession(proxy=settings.proxy_url)
    bot = Bot(token=settings.bot_token, session=session)
    dp = Dispatcher()
    dp.include_router(start.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
