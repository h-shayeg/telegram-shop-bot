from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import CartCallback, CheckoutCallback
from bot.checkout_keyboards import cancel_keyboard, confirm_order_keyboard, phone_keyboard
from bot.config import Settings
from bot.db.models import User
from bot.formatting import cart_lines, format_id, format_price, order_lines_text
from bot.keyboards import main_menu
from bot.order_keyboards import admin_open_order_keyboard
from bot.parsing import normalize_phone
from bot.services.cart import cart_total, get_cart
from bot.services.orders import EmptyCartError, PlacedOrder, StockError, place_order
from bot.states import Checkout
from bot.texts import DEFAULT_LANGUAGE, t, variants

router = Router(name="checkout")

NAME_LIMIT = 255
ADDRESS_LIMIT = 500

CANCEL_TEXTS = variants("checkout.cancel_button")
MENU_TEXTS = (
    variants("menu.products")
    | variants("menu.cart")
    | variants("menu.orders")
    | variants("menu.language")
)
# Commands, menu buttons and the cancel button are never taken as form answers
FORM_TEXT = F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_TEXTS | CANCEL_TEXTS)


async def _send(callback: CallbackQuery, text: str, markup: ReplyKeyboardMarkup | None = None) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(text, reply_markup=markup)


async def _remove_buttons(callback: CallbackQuery) -> None:
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(CartCallback.filter(F.action == "checkout"))
async def start_checkout(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str
) -> None:
    if not await get_cart(session, user.id):
        await callback.answer(t("checkout.cart_empty", lang), show_alert=True)
        return
    await callback.answer()
    await state.set_state(Checkout.name)
    await _send(callback, t("checkout.ask_name", lang), cancel_keyboard(lang))


@router.message(StateFilter(Checkout), F.text.in_(CANCEL_TEXTS))
@router.message(StateFilter(Checkout), Command("cancel"))
async def cancel_checkout(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("checkout.cancelled", lang), reply_markup=main_menu(lang))


@router.message(Checkout.name, FORM_TEXT)
async def got_name(message: Message, state: FSMContext, lang: str) -> None:
    name = (message.text or "").strip()
    if len(name) > NAME_LIMIT:
        await message.answer(t("common.too_long", lang, limit=NAME_LIMIT))
        return
    await state.update_data(name=name)
    await state.set_state(Checkout.phone)
    await message.answer(t("checkout.ask_phone", lang), reply_markup=phone_keyboard(lang))


async def _save_phone(message: Message, state: FSMContext, lang: str, phone: str | None) -> None:
    if phone is None:
        await message.answer(t("checkout.invalid_phone", lang))
        return
    await state.update_data(phone=phone)
    await state.set_state(Checkout.address)
    await message.answer(t("checkout.ask_address", lang), reply_markup=cancel_keyboard(lang))


@router.message(Checkout.phone, F.contact)
async def got_contact(message: Message, state: FSMContext, lang: str) -> None:
    contact = message.contact
    # Accept only the customer's own number, not a contact they forwarded
    own = contact is not None and message.from_user is not None and contact.user_id == message.from_user.id
    phone = normalize_phone(contact.phone_number) if own and contact else None
    # Telegram shares numbers in international form without the leading "+"
    if phone is not None and not phone.startswith(("+", "0")):
        phone = "+" + phone
    await _save_phone(message, state, lang, phone)


@router.message(Checkout.phone, FORM_TEXT)
async def got_phone_text(message: Message, state: FSMContext, lang: str) -> None:
    await _save_phone(message, state, lang, normalize_phone(message.text))


@router.message(Checkout.address, FORM_TEXT)
async def got_address(
    message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str
) -> None:
    address = (message.text or "").strip()
    if len(address) > ADDRESS_LIMIT:
        await message.answer(t("common.too_long", lang, limit=ADDRESS_LIMIT))
        return
    items = await get_cart(session, user.id)
    if not items:
        await state.clear()
        await message.answer(t("checkout.cart_empty", lang), reply_markup=main_menu(lang))
        return
    await state.update_data(address=address)
    await state.set_state(Checkout.confirm)
    data = await state.get_data()
    summary = t(
        "checkout.summary",
        lang,
        items=order_lines_text(cart_lines(items), lang),
        total=format_price(cart_total(items), lang),
        name=data["name"],
        phone=data["phone"],
        address=address,
    )
    await message.answer(summary, reply_markup=confirm_order_keyboard(lang))


async def _notify_admins(bot: Bot, session: AsyncSession, settings: Settings, placed: PlacedOrder, data: dict) -> None:
    for admin_id in settings.admin_ids:
        admin = await session.get(User, admin_id)
        admin_lang = admin.language if admin else DEFAULT_LANGUAGE
        text = t(
            "admin.new_order",
            admin_lang,
            order_id=format_id(placed.order_id, admin_lang),
            items=order_lines_text(placed.lines, admin_lang),
            total=format_price(placed.total, admin_lang),
            name=data["name"],
            phone=data["phone"],
            address=data["address"],
        )
        # An admin who never started the bot cannot receive messages; skip them
        with suppress(TelegramAPIError):
            await bot.send_message(
                admin_id, text, reply_markup=admin_open_order_keyboard(placed.order_id, admin_lang)
            )


@router.callback_query(Checkout.confirm, CheckoutCallback.filter(F.action == "confirm"))
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    lang: str,
    bot: Bot,
    settings: Settings,
) -> None:
    data = await state.get_data()
    await state.clear()
    await callback.answer()
    await _remove_buttons(callback)
    try:
        placed = await place_order(session, user.id, data["name"], data["phone"], data["address"])
    except EmptyCartError:
        await _send(callback, t("checkout.cart_empty", lang), main_menu(lang))
        return
    except StockError as error:
        items = "\n".join(f"- {name}" for name in error.product_names)
        await _send(callback, t("checkout.stock_problem", lang, items=items), main_menu(lang))
        return
    await _send(
        callback,
        t("checkout.placed", lang, order_id=format_id(placed.order_id, lang)),
        main_menu(lang),
    )
    await _notify_admins(bot, session, settings, placed, data)


@router.callback_query(CheckoutCallback.filter(F.action == "cancel"))
async def cancel_checkout_button(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.answer()
    await _remove_buttons(callback)
    await _send(callback, t("checkout.cancelled", lang), main_menu(lang))


@router.callback_query(CheckoutCallback.filter())
async def stale_checkout_button(callback: CallbackQuery) -> None:
    # For example "Confirm" pressed again after the order was already placed
    await callback.answer()
    await _remove_buttons(callback)
