from contextlib import suppress
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto, Message

CAPTION_LIMIT = 1024  # Telegram's limit for a photo caption


def _caption(text: str) -> str:
    return text if len(text) <= CAPTION_LIMIT else text[: CAPTION_LIMIT - 1] + "…"


async def replace_message(
    message: Any, text: str, markup: InlineKeyboardMarkup | None, photo: str | None = None
) -> None:
    """Turn `message` into a new screen.

    Telegram can edit a text message into another text, or a photo into another
    photo, but not one into the other; in that case the old message is deleted
    and a new one is sent.
    """
    has_photo = bool(message.photo)
    if (photo is not None) == has_photo:
        # Ignore "message is not modified" when the same button is tapped twice
        with suppress(TelegramBadRequest):
            if photo is None:
                await message.edit_text(text, reply_markup=markup)
            else:
                media = InputMediaPhoto(media=photo, caption=_caption(text))
                await message.edit_media(media, reply_markup=markup)
        return
    with suppress(TelegramBadRequest):
        await message.delete()
    if photo is None:
        await message.answer(text, reply_markup=markup)
    else:
        await message.answer_photo(photo, caption=_caption(text), reply_markup=markup)


async def show_screen(
    callback: CallbackQuery,
    text: str,
    markup: InlineKeyboardMarkup | None,
    photo: str | None = None,
) -> None:
    """Show a new screen in place of the message whose button was pressed."""
    if isinstance(callback.message, Message):
        await replace_message(callback.message, text, markup, photo)
