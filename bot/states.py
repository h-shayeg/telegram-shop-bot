from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    stock = State()
    photo = State()
    confirm = State()


class AddCategory(StatesGroup):
    name = State()


class EditProduct(StatesGroup):
    value = State()


class Checkout(StatesGroup):
    name = State()
    phone = State()
    address = State()
    confirm = State()
