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


class CheckoutCallback(CallbackData, prefix="co"):
    # action: "confirm" or "cancel"
    action: str


class OrderCallback(CallbackData, prefix="ord"):
    # Customer side. action: "list", "view" or "cancel"
    action: str
    id: int = 0


class AdminOrderCallback(CallbackData, prefix="ao"):
    # Admin side. action: "list", "view" or "set" (status is the new status for "set")
    action: str
    id: int = 0
    status: str = ""
