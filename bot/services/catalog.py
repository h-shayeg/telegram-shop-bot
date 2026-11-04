from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Category, Product


async def list_categories(session: AsyncSession) -> Sequence[Category]:
    """Active categories that have at least one active product."""
    stmt = (
        select(Category)
        .where(Category.is_active, Category.products.any(Product.is_active))
        .order_by(Category.id)
    )
    return (await session.scalars(stmt)).all()


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    category = await session.get(Category, category_id)
    return category if category is not None and category.is_active else None


async def list_products(session: AsyncSession, category_id: int) -> Sequence[Product]:
    stmt = (
        select(Product)
        .where(Product.category_id == category_id, Product.is_active)
        .order_by(Product.id)
    )
    return (await session.scalars(stmt)).all()


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    product = await session.get(Product, product_id)
    return product if product is not None and product.is_active else None
