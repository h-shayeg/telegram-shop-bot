from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Category, Product


async def list_all_categories(session: AsyncSession) -> Sequence[Category]:
    """Every category, hidden ones included (the admin sees everything)."""
    return (await session.scalars(select(Category).order_by(Category.id))).all()


async def list_all_products(session: AsyncSession, category_id: int) -> Sequence[Product]:
    stmt = select(Product).where(Product.category_id == category_id).order_by(Product.id)
    return (await session.scalars(stmt)).all()


async def category_name_exists(session: AsyncSession, name: str) -> bool:
    return await session.scalar(select(Category.id).where(Category.name == name)) is not None
