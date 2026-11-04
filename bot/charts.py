"""Small, dependency-light charts drawn with Pillow and sent to Telegram as PNG images.

Styling follows a simple, accessible scheme: one blue series on a light surface,
hairline gridlines, columns at most 24px wide with rounded tops, and a value
label only on the tallest column.
"""

from io import BytesIO
from math import ceil, floor, log10

from PIL import Image, ImageDraw, ImageFont

SCALE = 2  # draw at 2x so the image stays sharp on phone screens
WIDTH, HEIGHT = 640, 360

SURFACE = "#fcfcfb"
BAR = "#2a78d6"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
MUTED = "#898781"
TEXT = "#0b0b0b"


def nice_step(max_value: float, ticks: int = 4) -> float:
    """A round tick step (1, 2, 2.5 or 5 times a power of ten) covering max_value."""
    if max_value <= 0:
        return 1
    raw = max_value / ticks
    power = 10 ** floor(log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        if factor * power >= raw:
            return factor * power
    return 10 * power


def _tick_label(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.1f}"


def column_chart(labels: list[str], values: list[float]) -> bytes:
    """A single-series column chart; returns PNG bytes."""
    s = SCALE
    image = Image.new("RGB", (WIDTH * s, HEIGHT * s), SURFACE)
    draw = ImageDraw.Draw(image)
    axis_font = ImageFont.load_default(size=11 * s)
    value_font = ImageFont.load_default(size=12 * s)

    step = nice_step(max(values, default=0))
    top_value = step * max(1, ceil(max(values, default=0) / step))
    tick_values = [step * i for i in range(int(round(top_value / step)) + 1)]

    left = 16 * s + max(draw.textlength(_tick_label(v), font=axis_font) for v in tick_values)
    right, top, bottom = WIDTH * s - 16 * s, 28 * s, HEIGHT * s - 32 * s
    plot_height = bottom - top

    def y_of(value: float) -> float:
        return bottom - plot_height * (value / top_value)

    # Gridlines and y-axis labels (hairline, recessive)
    for value in tick_values:
        y = y_of(value)
        if value > 0:
            draw.line([(left, y), (right, y)], fill=GRID, width=1 * s)
        label = _tick_label(value)
        width = draw.textlength(label, font=axis_font)
        draw.text((left - 8 * s - width, y), label, fill=MUTED, font=axis_font, anchor="lm")

    # Columns: at most 24px wide and never filling their slot, rounded tops
    slot = (right - left) / max(len(values), 1)
    bar_width = min(24 * s, slot * 0.6)
    label_every = max(1, ceil(len(labels) / 8))
    tallest = max(range(len(values)), key=lambda i: values[i]) if values else -1
    for i, (label, value) in enumerate(zip(labels, values, strict=True)):
        center = left + slot * (i + 0.5)
        x0, x1 = center - bar_width / 2, center + bar_width / 2
        y = y_of(value)
        if value > 0:
            radius = min(4 * s, (bottom - y) / 2, bar_width / 2)
            draw.rounded_rectangle(
                (x0, y, x1, bottom), radius=radius, fill=BAR, corners=(True, True, False, False)
            )
        # Count from the last day so today is always labelled and labels never collide
        if (len(labels) - 1 - i) % label_every == 0:
            draw.text((center, bottom + 8 * s), label, fill=MUTED, font=axis_font, anchor="mt")
        if i == tallest and value > 0:
            draw.text((center, y - 6 * s), _tick_label(value), fill=TEXT, font=value_font, anchor="mb")

    # Baseline last, so columns sit on it
    draw.line([(left, bottom), (right, bottom)], fill=BASELINE, width=1 * s)

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
