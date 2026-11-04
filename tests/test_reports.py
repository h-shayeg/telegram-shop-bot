from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from bot.charts import column_chart, nice_step
from bot.db.models import Order, OrderItem, OrderStatus
from bot.handlers.admin_reports import day_label, report_text
from bot.services.reports import build_report

TEHRAN = ZoneInfo("Asia/Tehran")
TODAY = date(2026, 11, 4)


def order(created_utc: datetime, status: OrderStatus, items: list[tuple[str, int, int]]) -> Order:
    result = Order(
        id=1,
        user_id=1,
        status=status,
        customer_name="A",
        phone="0",
        address="X",
        total_price=sum(q * p for _, q, p in items),
        created_at=created_utc,
    )
    result.items = [OrderItem(product_name=n, quantity=q, unit_price=p) for n, q, p in items]
    return result


def test_report_counts_sales_and_skips_cancelled_orders() -> None:
    orders = [
        order(datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc), OrderStatus.NEW, [("Mug", 2, 100)]),
        order(datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc), OrderStatus.DELIVERED, [("Pen", 5, 10), ("Mug", 1, 100)]),
        order(datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc), OrderStatus.CANCELLED, [("Mug", 9, 100)]),
    ]
    report = build_report(orders, 7, TODAY, TEHRAN)
    assert report.order_count == 2
    assert report.revenue == 350
    assert report.cancelled_count == 1
    assert report.average_order == 175
    assert report.top_products == [("Pen", 5, 50), ("Mug", 3, 300)]
    assert len(report.daily) == 7 and report.daily[-1] == (TODAY, 200)


def test_days_follow_the_shop_time_zone() -> None:
    # 21:00 UTC on Nov 3 is already 00:30 on Nov 4 in Tehran
    late = order(datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc), OrderStatus.NEW, [("Mug", 1, 100)])
    report = build_report([late], 7, TODAY, TEHRAN)
    assert dict(report.daily)[TODAY] == 100


def test_orders_outside_the_period_are_ignored() -> None:
    old = order(datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc), OrderStatus.NEW, [("Mug", 1, 100)])
    assert build_report([old], 7, TODAY, TEHRAN).order_count == 0


def test_report_text_lists_best_sellers() -> None:
    orders = [order(datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc), OrderStatus.NEW, [("Mug", 2, 1000)])]
    text = report_text(build_report(orders, 7, TODAY, TEHRAN), "en")
    assert "Orders: 1" in text and "2,000 Toman" in text and "1. Mug" in text


def test_empty_report_says_no_sales() -> None:
    assert "No sales yet." in report_text(build_report([], 7, TODAY, TEHRAN), "en")


def test_tick_steps_are_round_numbers() -> None:
    assert nice_step(1000) == 250
    assert nice_step(37) == 10
    assert nice_step(0) == 1


def test_day_labels() -> None:
    assert day_label(TODAY, "en") == "11-04"
    assert day_label(TODAY, "fa") == "08/13"


def test_chart_is_a_png_image() -> None:
    png = column_chart(["a", "b", "c"], [0, 120.5, 30])
    assert png.startswith(b"\x89PNG")
