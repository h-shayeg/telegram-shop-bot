from bot.db.models import CartItem, Product
from bot.formatting import cart_text
from bot.keyboards import cart_keyboard
from bot.services.cart import cart_total


def make_item(product_id: int, price: int, quantity: int) -> CartItem:
    product = Product(id=product_id, category_id=1, name=f"P{product_id}", price=price, stock=10, is_active=True)
    return CartItem(id=product_id, user_id=1, product_id=product_id, quantity=quantity, product=product)


def test_total_adds_up_all_lines() -> None:
    items = [make_item(1, 1000, 2), make_item(2, 500, 3)]
    assert cart_total(items) == 3500


def test_cart_text_shows_lines_and_total() -> None:
    text = cart_text([make_item(1, 1000, 2)], "en")
    assert "P1" in text and "2 × 1,000 Toman = 2,000 Toman" in text and "Total: 2,000 Toman" in text


def test_empty_cart_text_and_no_keyboard() -> None:
    assert cart_text([], "en") == "🛒 Your cart is empty."
    assert cart_keyboard([], "en") is None


def test_cart_keyboard_has_plus_minus_per_item() -> None:
    markup = cart_keyboard([make_item(5, 1000, 1)], "en")
    first_row = [button.callback_data for button in markup.inline_keyboard[0]]
    assert first_row == ["cart:dec:5", "cart:noop:0", "cart:inc:5"]
    assert markup.inline_keyboard[-1][0].callback_data == "cart:checkout:0"
