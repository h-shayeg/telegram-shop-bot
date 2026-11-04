import json

from bot.keyboards import main_menu
from bot.texts import DEFAULT_LANGUAGE, LOCALES_DIR, SUPPORTED_LANGUAGES, t, variants


def load(lang: str) -> dict[str, str]:
    return json.loads((LOCALES_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def test_all_languages_have_the_same_keys() -> None:
    expected = set(load(DEFAULT_LANGUAGE))
    for lang in SUPPORTED_LANGUAGES:
        assert set(load(lang)) == expected, f"keys differ in {lang}.json"


def test_no_empty_texts() -> None:
    for lang in SUPPORTED_LANGUAGES:
        for key, value in load(lang).items():
            assert value.strip(), f"empty text for {key} in {lang}.json"


def test_unknown_language_falls_back_to_default() -> None:
    assert t("menu.cart", "xx") == t("menu.cart", DEFAULT_LANGUAGE)


def test_placeholder_is_filled() -> None:
    assert "Hadi" in t("start.welcome", "en", name="Hadi")


def test_each_language_has_its_own_menu_button() -> None:
    assert len(variants("menu.products")) == len(SUPPORTED_LANGUAGES)


def test_main_menu_has_four_buttons() -> None:
    markup = main_menu("en")
    texts = [button.text for row in markup.keyboard for button in row]
    assert texts == [t(k, "en") for k in ("menu.products", "menu.cart", "menu.orders", "menu.language")]
