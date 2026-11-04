from aiogram.filters.callback_data import CallbackData


class LanguageCallback(CallbackData, prefix="lang"):
    code: str
