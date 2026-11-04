from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import CartItem, Order, OrderItem, OrderStatus, Product, User

# Which status an order may move to from each status
ALLOWED_TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.NEW: (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
    OrderStatus.CONFIRMED: (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
    OrderStatus.SHIPPED: (OrderStatus.DELIVERED,),
    OrderStatus.DELIVERED: (),
    OrderStatus.CANCELLED: (),
}
OPEN_STATUSES = (OrderStatus.NEW, OrderStatus.CONFIRMED, OrderStatus.SHIPPED)


class EmptyCartError(Exception):
    pass


class StockError(Exception):
    def __init__(self, product_names: list[str]) -> None:
        super().__init__(", ".join(product_names))
        self.product_names = product_names


class OrderNotFoundError(Exception):
    pass


class OrderStatusError(Exception):
    """The requested status change is not allowed from the order's current status."""


@dataclass(frozen=True)
class PlacedOrder:
    order_id: int
    total: int
    lines: list[tuple[str, int, int]]  # (product name, quantity, unit price)


async def place_order(
    session: AsyncSession, user_id: int, name: str, phone: str, address: str
) -> PlacedOrder:
    """Turn the user's cart into an order in one transaction.

    Stock is checked and reduced while the product rows are locked, so two
    customers cannot buy the last item at the same time.
    """
    cart = (
        await session.scalars(
            select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)
        )
    ).all()
    if not cart:
        raise EmptyCartError()

    product_ids = [item.product_id for item in cart]
    locked = await session.scalars(
        select(Product).where(Product.id.in_(product_ids)).with_for_update()
    )
    products = {product.id: product for product in locked}

    problems = [
        products[item.product_id].name
        for item in cart
        if not products[item.product_id].is_active
        or products[item.product_id].stock < item.quantity
    ]
    if problems:
        await session.rollback()
        raise StockError(problems)

    lines: list[tuple[str, int, int]] = []
    order = Order(user_id=user_id, customer_name=name, phone=phone, address=address, total_price=0)
    for item in cart:
        product = products[item.product_id]
        product.stock -= item.quantity
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
            )
        )
        lines.append((product.name, item.quantity, product.price))
    order.total_price = sum(quantity * price for _, quantity, price in lines)
    session.add(order)

    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    user = await session.get(User, user_id)
    if user is not None:
        user.phone = phone
    await session.commit()
    return PlacedOrder(order_id=order.id, total=order.total_price, lines=lines)


def _with_items(lock: bool = False):  # type: ignore[no-untyped-def]
    stmt = select(Order).options(selectinload(Order.items))
    return stmt.with_for_update(of=Order) if lock else stmt


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.scalar(_with_items().where(Order.id == order_id))


async def list_user_orders(session: AsyncSession, user_id: int, limit: int = 10) -> Sequence[Order]:
    stmt = _with_items().where(Order.user_id == user_id).order_by(Order.id.desc()).limit(limit)
    return (await session.scalars(stmt)).all()


async def list_open_orders(session: AsyncSession, limit: int = 20) -> Sequence[Order]:
    stmt = _with_items().where(Order.status.in_(OPEN_STATUSES)).order_by(Order.id.desc()).limit(limit)
    return (await session.scalars(stmt)).all()


async def change_status(
    session: AsyncSession, order_id: int, new_status: OrderStatus, *, customer_id: int | None = None
) -> Order:
    """Move an order to a new status. Cancelling puts the items back in stock.

    With customer_id, only that customer's own order can be changed, and only
    from "new" to "cancelled".
    """
    order = await session.scalar(_with_items(lock=True).where(Order.id == order_id))
    owned = order is not None and (customer_id is None or order.user_id == customer_id)
    if order is None or not owned:
        await session.rollback()
        raise OrderNotFoundError()
    allowed = ALLOWED_TRANSITIONS[order.status]
    if customer_id is not None:
        allowed = (OrderStatus.CANCELLED,) if order.status == OrderStatus.NEW else ()
    if new_status not in allowed:
        await session.rollback()
        raise OrderStatusError()

    if new_status == OrderStatus.CANCELLED:
        for item in order.items:
            if item.product_id is not None:
                product = await session.get(Product, item.product_id, with_for_update=True)
                if product is not None:
                    product.stock += item.quantity
    order.status = new_status
    await session.commit()
    return order
