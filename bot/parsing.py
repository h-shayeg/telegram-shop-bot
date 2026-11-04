# Persian (U+06F0..U+06F9) and Arabic-Indic (U+0660..U+0669) digits -> ASCII digits
_DIGITS = str.maketrans(
    {**{chr(0x06F0 + i): str(i) for i in range(10)}, **{chr(0x0660 + i): str(i) for i in range(10)}}
)
# Thousands separators people type: comma, Persian/Arabic separators, spaces, underscore, ZWNJ
_SEPARATORS = (",", "\u066c", "\u060c", " ", "_", "\u200c")
_MAX_DIGITS = 12


def parse_int(text: str | None) -> int | None:
    """Read a whole, non-negative number typed by a person; return None if it is not one."""
    if text is None:
        return None
    value = text.strip().translate(_DIGITS)
    for separator in _SEPARATORS:
        value = value.replace(separator, "")
    if not value or not (value.isascii() and value.isdigit()) or len(value) > _MAX_DIGITS:
        return None
    return int(value)
