from aiogram.filters import Filter
from aiogram.types import TelegramObject, User

from bot.config import Settings


class IsAdmin(Filter):
    """Passes only for Telegram users listed in ADMIN_IDS."""

    async def __call__(
        self, event: TelegramObject, settings: Settings, event_from_user: User | None = None
    ) -> bool:
        return event_from_user is not None and event_from_user.id in settings.admin_ids
