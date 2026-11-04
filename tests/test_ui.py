import asyncio
from typing import Any

from bot.ui import CAPTION_LIMIT, _caption, replace_message


class FakeMessage:
    """Records which Telegram calls replace_message makes."""

    def __init__(self, has_photo: bool) -> None:
        self.photo = ["a photo"] if has_photo else None
        self.calls: list[str] = []

    async def edit_text(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append("edit_text")

    async def edit_media(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append("edit_media")

    async def delete(self) -> None:
        self.calls.append("delete")

    async def answer(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append("answer")

    async def answer_photo(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append("answer_photo")


def run(has_photo: bool, photo: str | None) -> list[str]:
    message = FakeMessage(has_photo)
    asyncio.run(replace_message(message, "text", None, photo=photo))
    return message.calls


def test_text_to_text_is_edited_in_place() -> None:
    assert run(has_photo=False, photo=None) == ["edit_text"]


def test_photo_to_photo_is_edited_in_place() -> None:
    assert run(has_photo=True, photo="new") == ["edit_media"]


def test_text_to_photo_sends_a_new_message() -> None:
    assert run(has_photo=False, photo="new") == ["delete", "answer_photo"]


def test_photo_to_text_sends_a_new_message() -> None:
    assert run(has_photo=True, photo=None) == ["delete", "answer"]


def test_long_captions_are_cut_to_the_telegram_limit() -> None:
    assert len(_caption("x" * 5000)) == CAPTION_LIMIT
    assert _caption("short") == "short"
