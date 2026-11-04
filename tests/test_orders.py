from datetime import UTC, datetime

from bot.db.models import Order, OrderItem, OrderStatus
from bot.formatting import format_date, order_text, status_label
from bot.order_keyboards import admin_order_keyboard, customer_order_keyboard
from bot.services.orders import ALLOWED_TRANSITIONS
from bot.texts import SUPPORTED_LANGUAGES

PERSIAN = {str(i): chr(0x06F0 + i) for i in range(10)}


def persian(text: str) -> str:
    return "".join(PERSIAN.get(ch, ch) for ch in text)


def make_order(status: OrderStatus) -> Order:
    order = Order(
        id=12,
        user_id=1,
        status=status,
        customer_name="Ali",
        phone="09121234567",
        address="Tehran",
        total_price=2000,
        created_at=datetime(2026, 11, 4, 13, 30, tzinfo=UTC),
    )
    order.items = [OrderItem(product_id=1, product_name="Mug", unit_price=1000, quantity=2)]
    return order


def test_every_status_has_a_label_in_every_language() -> None:
    for lang in SUPPORTED_LANGUAGES:
        for status in OrderStatus:
            assert status_label(status, lang)


def test_finished_orders_cannot_change() -> None:
    assert ALLOWED_TRANSITIONS[OrderStatus.DELIVERED] == ()
    assert ALLOWED_TRANSITIONS[OrderStatus.CANCELLED] == ()
    assert OrderStatus.CANCELLED not in ALLOWED_TRANSITIONS[OrderStatus.SHIPPED]


def test_dates_use_shop_time_zone_and_calendar() -> None:
    moment = datetime(2026, 11, 4, 13, 30, tzinfo=UTC)  # 17:00 in Tehran
    assert format_date(moment, "en") == "2026-11-04 17:00"
    assert format_date(moment, "fa") == persian("1405/08/13 17:00")


def test_order_text_contains_the_essentials() -> None:
    text = order_text(make_order(OrderStatus.NEW), "en")
    assert "#12" in text and "Mug" in text and "2,000 Toman" in text and "Received" in text


def test_only_new_orders_can_be_cancelled_by_the_customer() -> None:
    def callbacks(order: Order) -> list[str]:
        return [b.callback_data for row in customer_order_keyboard(order, "en").inline_keyboard for b in row]

    assert "ord:cancel:12" in callbacks(make_order(OrderStatus.NEW))
    assert "ord:cancel:12" not in callbacks(make_order(OrderStatus.CONFIRMED))


def test_admin_sees_only_allowed_next_statuses() -> None:
    markup = admin_order_keyboard(make_order(OrderStatus.CONFIRMED), "en")
    data = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert data == ["ao:set:12:shipped", "ao:set:12:cancelled", "ao:list:0:"]
