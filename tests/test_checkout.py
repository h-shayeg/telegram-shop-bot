import asyncio

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery, SendMessage

from bot.formatting import format_id, order_lines_text
from bot.middlewares.requests import IgnoreExpiredCallbackAnswers
from bot.parsing import normalize_phone

PERSIAN = {str(i): chr(0x06F0 + i) for i in range(10)}


def persian(text: str) -> str:
    return "".join(PERSIAN.get(ch, ch) for ch in text)


def test_phone_formats() -> None:
    assert normalize_phone("09121234567") == "09121234567"
    assert normalize_phone("+98 912 123 4567") == "+989121234567"
    assert normalize_phone("0912-123-4567") == "09121234567"
    assert normalize_phone(persian("09121234567")) == "09121234567"


def test_bad_phones() -> None:
    for text in ["", "abc", "12", "+", "0912 123 4567 8888 99", None]:
        assert normalize_phone(text) is None, text


def test_order_id_has_no_separators() -> None:
    assert format_id(1234, "en") == "1234"
    assert format_id(1234, "fa") == persian("1234")


def test_order_lines() -> None:
    text = order_lines_text([("Mug", 2, 1000), ("Pen", 1, 500)], "en")
    assert "2 × 1,000 Toman = 2,000 Toman" in text and "Pen" in text


def _run(middleware: IgnoreExpiredCallbackAnswers, method: object, error: Exception) -> object:
    async def failing(bot: object, method: object) -> object:
        raise error

    return asyncio.run(middleware(failing, None, method))  # type: ignore[arg-type]


def test_expired_button_answer_is_ignored() -> None:
    method = AnswerCallbackQuery(callback_query_id="1")
    error = TelegramBadRequest(method=method, message="Bad Request: query is too old and response timeout expired")
    assert _run(IgnoreExpiredCallbackAnswers(), method, error) is True


def test_other_errors_are_not_hidden() -> None:
    method = SendMessage(chat_id=1, text="x")
    error = TelegramBadRequest(method=method, message="Bad Request: chat not found")
    with pytest.raises(TelegramBadRequest):
        _run(IgnoreExpiredCallbackAnswers(), method, error)
