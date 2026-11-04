from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import CartItem, Product


async def get_cart(session: AsyncSession, user_id: int) -> Sequence[CartItem]:
    """Cart items whose product is still on sale, oldest first."""
    stmt = (
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id)
    )
    items = (await session.scalars(stmt)).all()
    return [item for item in items if item.product.is_active]


def cart_total(items: Sequence[CartItem]) -> int:
    return sum(item.quantity * item.product.price for item in items)


async def _get_item(session: AsyncSession, user_id: int, product_id: int) -> CartItem | None:
    stmt = select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    return await session.scalar(stmt)


async def add_to_cart(session: AsyncSession, user_id: int, product: Product) -> tuple[bool, int]:
    """Add one unit. Returns (added, quantity now in cart)."""
    item = await _get_item(session, user_id, product.id)
    current = item.quantity if item else 0
    if current + 1 > product.stock:
        return False, current
    if item is None:
        session.add(CartItem(user_id=user_id, product_id=product.id, quantity=1))
    else:
        item.quantity += 1
    await session.commit()
    return True, current + 1


async def change_quantity(
    session: AsyncSession, user_id: int, product_id: int, delta: int
) -> tuple[bool, int]:
    """Change the quantity by delta. Returns (changed, quantity now in cart). Zero removes the item."""
    item = await _get_item(session, user_id, product_id)
    if item is None:
        return False, 0
    product = await session.get(Product, product_id)
    new_quantity = item.quantity + delta
    if product is None or (delta > 0 and new_quantity > product.stock):
        return False, item.quantity
    if new_quantity <= 0:
        await session.delete(item)
        new_quantity = 0
    else:
        item.quantity = new_quantity
    await session.commit()
    return True, new_quantity


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()
