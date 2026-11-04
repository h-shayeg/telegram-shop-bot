from contextlib import suppress
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin_keyboards import (
    EDITABLE_FIELDS,
    admin_categories_keyboard,
    admin_menu_keyboard,
    admin_product_keyboard,
    admin_products_keyboard,
    confirm_keyboard,
)
from bot.callbacks import AdminCallback
from bot.db.models import Category, Product
from bot.filters import IsAdmin
from bot.formatting import admin_product_text
from bot.parsing import parse_int
from bot.services.admin import category_name_exists, list_all_categories, list_all_products
from bot.states import AddCategory, AddProduct, EditProduct
from bot.texts import t, variants

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

NAME_LIMIT = 200
CATEGORY_LIMIT = 100
DESCRIPTION_LIMIT = 1000

# Main-menu buttons and commands are never taken as form answers
MENU_TEXTS = (
    variants("menu.products")
    | variants("menu.cart")
    | variants("menu.orders")
    | variants("menu.language")
)
FORM_TEXT = F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_TEXTS)


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text, reply_markup=markup)


async def _send(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(text, reply_markup=markup)


async def _product_view(session: AsyncSession, product: Product, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    category = await session.get(Category, product.category_id)
    text = admin_product_text(
        name=product.name,
        category=category.name if category else "-",
        description=product.description,
        price=product.price,
        stock=product.stock,
        is_active=product.is_active,
        lang=lang,
    )
    text += "\n" + t("admin.has_photo" if product.photo_file_id else "admin.no_photo", lang)
    return text, admin_product_keyboard(product, lang)


# ---------- entry points ----------


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("admin.panel", lang), reply_markup=admin_menu_keyboard(lang))


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(t("admin.cancelled", lang), reply_markup=admin_menu_keyboard(lang))


@router.callback_query(AdminCallback.filter(F.action == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.answer()
    await _edit(callback, t("admin.panel", lang), admin_menu_keyboard(lang))


@router.callback_query(AdminCallback.filter(F.action == "cancel"))
async def cancel_button(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.answer(t("admin.cancelled", lang))
    await _edit(callback, t("admin.panel", lang), admin_menu_keyboard(lang))


# ---------- add category ----------


@router.callback_query(AdminCallback.filter(F.action == "add_category"))
async def add_category_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.answer()
    await state.set_state(AddCategory.name)
    await _send(callback, t("admin.ask_category_name", lang))


@router.message(AddCategory.name, FORM_TEXT)
async def add_category_name(
    message: Message, state: FSMContext, session: AsyncSession, lang: str
) -> None:
    name = (message.text or "").strip()
    if len(name) > CATEGORY_LIMIT:
        await message.answer(t("admin.too_long", lang, limit=CATEGORY_LIMIT))
        return
    if await category_name_exists(session, name):
        await message.answer(t("admin.category_exists", lang))
        return
    session.add(Category(name=name))
    await session.commit()
    await state.clear()
    await message.answer(
        t("admin.category_saved", lang, name=name), reply_markup=admin_menu_keyboard(lang)
    )


# ---------- add product ----------


@router.callback_query(AdminCallback.filter(F.action == "add_product"))
async def add_product_start(callback: CallbackQuery, session: AsyncSession, lang: str) -> None:
    categories = await list_all_categories(session)
    if not categories:
        await callback.answer(t("admin.no_categories", lang), show_alert=True)
        return
    await callback.answer()
    await _edit(
        callback,
        t("admin.choose_category", lang),
        admin_categories_keyboard(categories, "pick_category", lang),
    )


@router.callback_query(AdminCallback.filter(F.action == "pick_category"))
async def add_product_category(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
    session: AsyncSession,
    lang: str,
) -> None:
    category = await session.get(Category, callback_data.id)
    if category is None:
        await callback.answer(t("admin.not_found", lang), show_alert=True)
        return
    await callback.answer()
    await state.set_state(AddProduct.name)
    await state.update_data(category_id=category.id, category_name=category.name)
    await _send(callback, t("admin.ask_name", lang))


@router.message(AddProduct.name, FORM_TEXT)
async def add_product_name(message: Message, state: FSMContext, lang: str) -> None:
    name = (message.text or "").strip()
    if len(name) > NAME_LIMIT:
        await message.answer(t("admin.too_long", lang, limit=NAME_LIMIT))
        return
    await state.update_data(name=name)
    await state.set_state(AddProduct.description)
    await message.answer(t("admin.ask_description", lang))


@router.message(AddProduct.description, Command("skip"))
async def add_product_skip_description(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(description=None)
    await state.set_state(AddProduct.price)
    await message.answer(t("admin.ask_price", lang))


@router.message(AddProduct.description, FORM_TEXT)
async def add_product_description(message: Message, state: FSMContext, lang: str) -> None:
    description = (message.text or "").strip()
    if len(description) > DESCRIPTION_LIMIT:
        await message.answer(t("admin.too_long", lang, limit=DESCRIPTION_LIMIT))
        return
    await state.update_data(description=description)
    await state.set_state(AddProduct.price)
    await message.answer(t("admin.ask_price", lang))


@router.message(AddProduct.price, FORM_TEXT)
async def add_product_price(message: Message, state: FSMContext, lang: str) -> None:
    price = parse_int(message.text)
    if price is None:
        await message.answer(t("admin.invalid_number", lang))
        return
    await state.update_data(price=price)
    await state.set_state(AddProduct.stock)
    await message.answer(t("admin.ask_stock", lang))


@router.message(AddProduct.stock, FORM_TEXT)
async def add_product_stock(message: Message, state: FSMContext, lang: str) -> None:
    stock = parse_int(message.text)
    if stock is None:
        await message.answer(t("admin.invalid_number", lang))
        return
    await state.update_data(stock=stock)
    await state.set_state(AddProduct.photo)
    await message.answer(t("admin.ask_photo", lang))


async def _ask_confirmation(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(AddProduct.confirm)
    data: dict[str, Any] = await state.get_data()
    details = admin_product_text(
        name=data["name"],
        category=data["category_name"],
        description=data.get("description"),
        price=data["price"],
        stock=data["stock"],
        is_active=True,
        lang=lang,
    )
    details += "\n" + t("admin.has_photo" if data.get("photo") else "admin.no_photo", lang)
    await message.answer(
        t("admin.confirm_product", lang, details=details), reply_markup=confirm_keyboard(lang)
    )


@router.message(AddProduct.photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, lang: str) -> None:
    # Telegram sends several sizes; the last one is the largest
    await state.update_data(photo=message.photo[-1].file_id if message.photo else None)
    await _ask_confirmation(message, state, lang)


@router.message(AddProduct.photo, Command("skip"))
async def add_product_skip_photo(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(photo=None)
    await _ask_confirmation(message, state, lang)


@router.message(AddProduct.photo, ~F.text.in_(MENU_TEXTS))
async def add_product_photo_missing(message: Message, lang: str) -> None:
    await message.answer(t("admin.need_photo", lang))


@router.callback_query(AddProduct.confirm, AdminCallback.filter(F.action == "save"))
async def add_product_save(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str
) -> None:
    data = await state.get_data()
    product = Product(
        category_id=data["category_id"],
        name=data["name"],
        description=data.get("description"),
        price=data["price"],
        stock=data["stock"],
        photo_file_id=data.get("photo"),
    )
    session.add(product)
    await session.commit()
    await state.clear()
    await callback.answer(t("admin.product_saved", lang))
    text, markup = await _product_view(session, product, lang)
    await _edit(callback, text, markup)


# ---------- manage products ----------


@router.callback_query(AdminCallback.filter(F.action == "products"))
async def manage_products(callback: CallbackQuery, session: AsyncSession, lang: str) -> None:
    categories = await list_all_categories(session)
    if not categories:
        await callback.answer(t("admin.no_categories", lang), show_alert=True)
        return
    await callback.answer()
    await _edit(
        callback,
        t("admin.choose_category", lang),
        admin_categories_keyboard(categories, "category", lang),
    )


@router.callback_query(AdminCallback.filter(F.action == "category"))
async def admin_category(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, lang: str
) -> None:
    await callback.answer()
    products = await list_all_products(session, callback_data.id)
    text = t("admin.choose_product", lang) if products else t("admin.no_products", lang)
    await _edit(callback, text, admin_products_keyboard(products, lang))


@router.callback_query(AdminCallback.filter(F.action == "product"))
async def admin_product(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, lang: str
) -> None:
    product = await session.get(Product, callback_data.id)
    if product is None:
        await callback.answer(t("admin.not_found", lang), show_alert=True)
        return
    await callback.answer()
    text, markup = await _product_view(session, product, lang)
    await _edit(callback, text, markup)


@router.callback_query(AdminCallback.filter(F.action == "toggle"))
async def toggle_product(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, lang: str
) -> None:
    product = await session.get(Product, callback_data.id)
    if product is None:
        await callback.answer(t("admin.not_found", lang), show_alert=True)
        return
    product.is_active = not product.is_active
    await session.commit()
    await callback.answer(t("admin.updated", lang))
    text, markup = await _product_view(session, product, lang)
    await _edit(callback, text, markup)


# ---------- edit one field ----------


@router.callback_query(AdminCallback.filter(F.action == "edit"))
async def edit_start(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext, lang: str
) -> None:
    if callback_data.field not in EDITABLE_FIELDS:
        await callback.answer()
        return
    await callback.answer()
    await state.set_state(EditProduct.value)
    await state.update_data(product_id=callback_data.id, field=callback_data.field)
    prompts = {"description": "admin.ask_new_description", "photo": "admin.ask_new_photo"}
    await _send(callback, t(prompts.get(callback_data.field, "admin.ask_new_value"), lang))


async def _save_edit(
    message: Message, state: FSMContext, session: AsyncSession, lang: str, value: object
) -> None:
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])
    await state.clear()
    if product is None:
        await message.answer(t("admin.not_found", lang))
        return
    column = "photo_file_id" if data["field"] == "photo" else data["field"]
    setattr(product, column, value)
    await session.commit()
    text, markup = await _product_view(session, product, lang)
    await message.answer(t("admin.updated", lang))
    await message.answer(text, reply_markup=markup)


@router.message(EditProduct.value, Command("skip"))
async def edit_skip(message: Message, state: FSMContext, session: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    if data.get("field") in ("description", "photo"):
        await _save_edit(message, state, session, lang, None)
    else:
        await message.answer(t("admin.ask_new_value", lang))


@router.message(EditProduct.value, F.photo)
async def edit_photo(message: Message, state: FSMContext, session: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    if data.get("field") == "photo" and message.photo:
        await _save_edit(message, state, session, lang, message.photo[-1].file_id)
    else:
        await message.answer(t("admin.ask_new_value", lang))


@router.message(EditProduct.value, FORM_TEXT)
async def edit_value(message: Message, state: FSMContext, session: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    field = data.get("field")
    text = (message.text or "").strip()
    value: object
    if field == "photo":
        await message.answer(t("admin.need_photo", lang))
        return
    if field in ("price", "stock"):
        value = parse_int(text)
        if value is None:
            await message.answer(t("admin.invalid_number", lang))
            return
    else:
        limit = NAME_LIMIT if field == "name" else DESCRIPTION_LIMIT
        if len(text) > limit:
            await message.answer(t("admin.too_long", lang, limit=limit))
            return
        value = text
    await _save_edit(message, state, session, lang, value)


# Old buttons (for example "Save" after the form was cancelled): just stop the spinner
@router.callback_query(AdminCallback.filter())
async def stale_button(callback: CallbackQuery) -> None:
    await callback.answer()
