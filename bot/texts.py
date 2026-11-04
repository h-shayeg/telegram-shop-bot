import json
from functools import cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
SUPPORTED_LANGUAGES = ("fa", "en")
DEFAULT_LANGUAGE = "fa"


@cache
def _load(lang: str) -> dict[str, str]:
    with open(LOCALES_DIR / f"{lang}.json", encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str | None = None, **kwargs: object) -> str:
    """Return the text for `key` in `lang`, falling back to the default language."""
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    text = _load(lang).get(key) or _load(DEFAULT_LANGUAGE)[key]
    return text.format(**kwargs) if kwargs else text


def variants(key: str) -> set[str]:
    """All translations of `key`, used to match reply-keyboard buttons in any language."""
    return {_load(lang)[key] for lang in SUPPORTED_LANGUAGES}
