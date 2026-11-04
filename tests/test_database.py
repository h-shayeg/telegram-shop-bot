"""Tests that run the shop logic against a real PostgreSQL database.

They are skipped unless TEST_DATABASE_URL is set. That database is wiped before
every test, so its name must end with "_test" (never the real shop database).
"""

import asyncio
import os
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import bot.config  # noqa: F401  (loads .env)
from bot.db.base import Base
from bot.db.models import Category, Order, OrderStatus, Product, User
from bot.services.cart import add_to_cart, get_cart
from bot.services.orders import (
    OrderNotFoundError,
    OrderStatusError,
    StockError,
    change_status,
    get_order,
    place_order,
)
from bot.services.reports import sales_report

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set")

Sessions = async_sessionmaker[AsyncSession]


def run(scenario: Callable[[Sessions], Awaitable[None]]) -> None:
    """Run one scenario on empty tables."""
    database = make_url(TEST_DATABASE_URL).database or ""
    assert database.endswith("_test"), "TEST_DATABASE_URL must point to a database whose name ends with _test"

    async def main() -> None:
        engine = create_async_engine(TEST_DATABASE_URL)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
                await connection.run_sync(Base.metadata.create_all)
            await scenario(async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(main())


async def open_shop(sessions: Sessions, stock: int, price: int = 1000) -> int:
    """Two customers and one product. Returns the product id."""
    async with sessions() as session:
        product = Product(category=Category(name="Cups"), name="Mug", price=price, stock=stock)
        session.add_all([User(id=1, first_name="Ali"), User(id=2, first_name="Sara"), product])
        await session.commit()
        return product.id


async def fill_cart(sessions: Sessions, user_id: int, product_id: int, quantity: int) -> None:
    async with sessions() as session:
        product = await session.get(Product, product_id)
        assert product is not None
        for _ in range(quantity):
            added, _quantity = await add_to_cart(session, user_id, product)
            assert added


async def buy(sessions: Sessions, user_id: int) -> int:
    async with sessions() as session:
        placed = await place_order(session, user_id, "Ali", "09121234567", "Tehran")
        return placed.order_id


async def stock_of(sessions: Sessions, product_id: int) -> int:
    async with sessions() as session:
        product = await session.get(Product, product_id)
        assert product is not None
        return product.stock


def test_order_takes_items_out_of_stock_and_empties_the_cart() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=5)
        await fill_cart(sessions, 1, product_id, 2)
        order_id = await buy(sessions, 1)

        assert await stock_of(sessions, product_id) == 3
        async with sessions() as session:
            assert await get_cart(session, 1) == []
            order = await get_order(session, order_id)
            assert order is not None
            assert order.status == OrderStatus.NEW and order.total_price == 2000
            assert [(i.product_name, i.quantity, i.unit_price) for i in order.items] == [("Mug", 2, 1000)]
            customer = await session.get(User, 1)
            assert customer is not None and customer.phone == "09121234567"

    run(scenario)


def test_cart_never_holds_more_than_the_stock() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=2)
        await fill_cart(sessions, 1, product_id, 2)
        async with sessions() as session:
            product = await session.get(Product, product_id)
            assert product is not None
            assert await add_to_cart(session, 1, product) == (False, 2)

    run(scenario)


def test_order_is_refused_when_stock_ran_out_after_adding_to_cart() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=2)
        await fill_cart(sessions, 1, product_id, 2)
        async with sessions() as session:  # the shop lowers the stock in the meantime
            product = await session.get(Product, product_id)
            assert product is not None
            product.stock = 1
            await session.commit()

        with pytest.raises(StockError) as error:
            await buy(sessions, 1)
        assert error.value.product_names == ["Mug"]
        assert await stock_of(sessions, product_id) == 1
        async with sessions() as session:
            assert len(await get_cart(session, 1)) == 1  # the cart is kept so the customer can fix it
            assert await session.scalar(select(func.count(Order.id))) == 0

    run(scenario)


def test_two_customers_cannot_buy_the_last_item() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=1)
        await fill_cart(sessions, 1, product_id, 1)
        await fill_cart(sessions, 2, product_id, 1)

        async def try_to_buy(user_id: int) -> bool:
            try:
                await buy(sessions, user_id)
            except StockError:
                return False
            return True

        # Both customers press "Confirm" at the same moment
        results = await asyncio.gather(try_to_buy(1), try_to_buy(2))
        assert sorted(results) == [False, True]
        assert await stock_of(sessions, product_id) == 0

    run(scenario)


def test_cancelling_an_order_puts_the_items_back_in_stock() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=5)
        await fill_cart(sessions, 1, product_id, 2)
        order_id = await buy(sessions, 1)
        async with sessions() as session:
            order = await change_status(session, order_id, OrderStatus.CANCELLED)
            assert order.status == OrderStatus.CANCELLED
        assert await stock_of(sessions, product_id) == 5

    run(scenario)


def test_customers_can_cancel_only_their_own_new_orders() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=5)
        await fill_cart(sessions, 1, product_id, 1)
        order_id = await buy(sessions, 1)
        async with sessions() as session:
            with pytest.raises(OrderNotFoundError):  # someone else's order
                await change_status(session, order_id, OrderStatus.CANCELLED, customer_id=2)
            await change_status(session, order_id, OrderStatus.CONFIRMED)  # the shop confirms it
            with pytest.raises(OrderStatusError):  # too late for the customer to cancel
                await change_status(session, order_id, OrderStatus.CANCELLED, customer_id=1)
        assert await stock_of(sessions, product_id) == 4

    run(scenario)


def test_order_status_only_moves_forward() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=5)
        await fill_cart(sessions, 1, product_id, 1)
        order_id = await buy(sessions, 1)
        async with sessions() as session:
            with pytest.raises(OrderStatusError):
                await change_status(session, order_id, OrderStatus.SHIPPED)  # not confirmed yet
            for status in (OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED):
                await change_status(session, order_id, status)
            with pytest.raises(OrderStatusError):
                await change_status(session, order_id, OrderStatus.CANCELLED)  # already delivered

    run(scenario)


def test_sales_report_counts_only_orders_that_were_not_cancelled() -> None:
    async def scenario(sessions: Sessions) -> None:
        product_id = await open_shop(sessions, stock=10, price=1500)
        await fill_cart(sessions, 1, product_id, 3)
        await buy(sessions, 1)
        await fill_cart(sessions, 2, product_id, 1)
        cancelled_id = await buy(sessions, 2)
        async with sessions() as session:
            await change_status(session, cancelled_id, OrderStatus.CANCELLED)
            report = await sales_report(session, 7)
        assert (report.order_count, report.revenue, report.cancelled_count) == (1, 4500, 1)
        assert report.top_products == [("Mug", 3, 4500)]
        assert report.daily[-1][1] == 4500

    run(scenario)
