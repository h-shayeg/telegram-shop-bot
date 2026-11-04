from typing import Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery, TelegramMethod


class IgnoreExpiredCallbackAnswers(BaseRequestMiddleware):
    """Telegram rejects answers to button presses that are too old (for example presses
    made while the bot was off). Those answers only stop a loading spinner, so the
    rejection is ignored instead of stopping the handler."""

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[Any],
        bot: Bot,
        method: TelegramMethod[Any],
    ) -> Any:
        try:
            return await make_request(bot, method)
        except TelegramBadRequest as error:
            if isinstance(method, AnswerCallbackQuery) and "query is too old" in error.message:
                return True
            raise
