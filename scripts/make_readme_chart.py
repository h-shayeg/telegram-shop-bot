"""Draw the sample sales chart shown in the README (made-up numbers, not real sales).

Usage: python -m scripts.make_readme_chart
"""

from datetime import date, timedelta
from pathlib import Path

from bot.charts import column_chart
from bot.handlers.admin_reports import day_label

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "sales-chart.png"

# Daily sales of a small shop over 30 days, in thousand toman
SAMPLE_SALES = [
    1250, 980, 0, 1640, 2100, 1870, 760, 1320, 2480, 1900,
    0, 1150, 1730, 2260, 3050, 2410, 1380, 990, 1560, 2140,
    2720, 1810, 0, 1470, 2030, 2590, 3380, 2870, 1960, 2350,
]


def main() -> None:
    last_day = date(2026, 11, 4)
    days = [last_day - timedelta(days=i) for i in range(len(SAMPLE_SALES) - 1, -1, -1)]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(column_chart([day_label(day, "fa") for day in days], SAMPLE_SALES))
    print(f"Chart saved to {OUTPUT.relative_to(OUTPUT.parent.parent.parent)}")


if __name__ == "__main__":
    main()
