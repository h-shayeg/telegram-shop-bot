from aiogram.filters.callback_data import CallbackData


class LanguageCallback(CallbackData, prefix="lang"):
    code: str


class CatalogCallback(CallbackData, prefix="cat"):
    # action: "categories", "category" or "product"
    action: str
    id: int = 0


class CartCallback(CallbackData, prefix="cart"):
    action: str
    product_id: int = 0


class AdminCallback(CallbackData, prefix="adm"):
    action: str
    id: int = 0
    field: str = ""
