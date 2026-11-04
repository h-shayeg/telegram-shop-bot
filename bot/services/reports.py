from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import Order, OrderStatus
from bot.formatting import SHOP_TIMEZONE

TOP_PRODUCTS = 5


@dataclass(frozen=True)
class SalesReport:
    days: int
    order_count: int  # cancelled orders are not counted
    revenue: int
    cancelled_count: int
    daily: list[tuple[date, int]]  # every day of the period, oldest first
    top_products: list[tuple[str, int, int]]  # (name, quantity sold, revenue)

    @property
    def average_order(self) -> int:
        return self.revenue // self.order_count if self.order_count else 0


def build_report(orders: Sequence[Order], days: int, today: date, tz: tzinfo) -> SalesReport:
    """Summarise orders placed in the `days` days that end on `today` (shop time zone)."""
    first_day = today - timedelta(days=days - 1)
    per_day: dict[date, int] = {first_day + timedelta(days=i): 0 for i in range(days)}
    per_product: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    order_count = revenue = cancelled = 0

    for order in orders:
        day = order.created_at.astimezone(tz).date()
        if day not in per_day:
            continue
        if order.status == OrderStatus.CANCELLED:
            cancelled += 1
            continue
        order_count += 1
        revenue += order.total_price
        per_day[day] += order.total_price
        for item in order.items:
            per_product[item.product_name][0] += item.quantity
            per_product[item.product_name][1] += item.quantity * item.unit_price

    top = sorted(per_product.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0]))[:TOP_PRODUCTS]
    return SalesReport(
        days=days,
        order_count=order_count,
        revenue=revenue,
        cancelled_count=cancelled,
        daily=sorted(per_day.items()),
        top_products=[(name, quantity, total) for name, (quantity, total) in top],
    )


async def sales_report(session: AsyncSession, days: int, now: datetime | None = None) -> SalesReport:
    today = (now or datetime.now(SHOP_TIMEZONE)).astimezone(SHOP_TIMEZONE).date()
    start = datetime.combine(today - timedelta(days=days - 1), time.min, tzinfo=SHOP_TIMEZONE)
    stmt = select(Order).options(selectinload(Order.items)).where(Order.created_at >= start)
    orders = (await session.scalars(stmt)).all()
    return build_report(orders, days, today, SHOP_TIMEZONE)
