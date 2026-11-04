import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Hello! The shop bot is running.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    proxy_url = os.getenv("PROXY_URL") or None
    session = AiohttpSession(proxy=proxy_url)
    bot = Bot(token=os.environ["BOT_TOKEN"], session=session)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
