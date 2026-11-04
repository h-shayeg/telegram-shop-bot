from contextlib import suppress
from datetime import date

import jdatetime
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminCallback, ReportCallback
from bot.charts import column_chart
from bot.filters import IsAdmin
from bot.formatting import format_number, format_price
from bot.services.reports import SalesReport, sales_report
from bot.texts import t

router = Router(name="admin_reports")
router.callback_query.filter(IsAdmin())

PERIODS = (7, 30)


def report_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for days in PERIODS:
        builder.button(text=t(f"admin.report_{days}", lang), callback_data=ReportCallback(days=days))
    builder.button(text=t("button.back", lang), callback_data=AdminCallback(action="menu"))
    builder.adjust(2, 1)
    return builder.as_markup()


def report_text(report: SalesReport, lang: str) -> str:
    top = "\n".join(
        t(
            "admin.report_top_line",
            lang,
            rank=format_number(rank, lang),
            name=name,
            quantity=format_number(quantity, lang),
            revenue=format_price(revenue, lang),
        )
        for rank, (name, quantity, revenue) in enumerate(report.top_products, start=1)
    )
    return t(
        "admin.report_text",
        lang,
        days=format_number(report.days, lang),
        orders=format_number(report.order_count, lang),
        revenue=format_price(report.revenue, lang),
        average=format_price(report.average_order, lang),
        cancelled=format_number(report.cancelled_count, lang),
        top=top or t("admin.report_no_sales", lang),
    )


def day_label(day: date, lang: str) -> str:
    """Short date under each column: Persian calendar for Persian, month-day otherwise."""
    if lang == "fa":
        return jdatetime.date.fromgregorian(date=day).strftime("%m/%d")
    return day.strftime("%m-%d")


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(ReportCallback.filter(F.days == 0))
async def choose_period(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await _edit(callback, t("admin.report_choose", lang), report_keyboard(lang))


@router.callback_query(ReportCallback.filter())
async def show_report(
    callback: CallbackQuery, callback_data: ReportCallback, session: AsyncSession, lang: str
) -> None:
    days = callback_data.days if callback_data.days in PERIODS else PERIODS[0]
    await callback.answer()
    report = await sales_report(session, days)
    await _edit(callback, report_text(report, lang), report_keyboard(lang))
    if report.revenue > 0 and isinstance(callback.message, Message):
        png = column_chart(
            [day_label(day, lang) for day, _ in report.daily],
            [amount / 1000 for _, amount in report.daily],  # thousand toman
        )
        await callback.message.answer_photo(
            BufferedInputFile(png, filename=f"sales-{days}-days.png"),
            caption=t("admin.report_chart_caption", lang, days=format_number(days, lang)),
        )
