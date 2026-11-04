from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.db.models import User
from bot.texts import DEFAULT_LANGUAGE


async def upsert_user(session: AsyncSession, tg_user: TelegramUser) -> User:
    """Create the user on first contact, keep name and username up to date afterwards."""
    stmt = (
        insert(User)
        .values(
            id=tg_user.id,
            first_name=tg_user.first_name,
            username=tg_user.username,
            language=DEFAULT_LANGUAGE,
        )
        .on_conflict_do_update(
            index_elements=["id"],
            set_={"first_name": tg_user.first_name, "username": tg_user.username},
        )
        .returning(User)
    )
    result = await session.scalars(stmt, execution_options={"populate_existing": True})
    user = result.one()
    await session.commit()
    return user


class DbSessionMiddleware(BaseMiddleware):
    """Opens one database session per update and loads the current user."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            tg_user = data.get("event_from_user")
            if tg_user is not None:
                user = await upsert_user(session, tg_user)
                data["user"] = user
                data["lang"] = user.language
            return await handler(event, data)
