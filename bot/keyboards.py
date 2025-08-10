# bot/keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot import sheets  

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌍 GEO"), KeyboardButton(text="📋 Все офферы")],
            [KeyboardButton(text="🏆 Топ недели"), KeyboardButton(text="🔄 Обновить")],
        ],
        resize_keyboard=True
    )

async def geos_keyboard() -> InlineKeyboardMarkup:
    geos = await sheets.geos()
    keyboard = [
        [InlineKeyboardButton(text=geo, callback_data=f"geo:{geo}")]
        for geo in geos
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def offers_keyboard(offers) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=offer.name, callback_data=f"offer:{offer.name}")]
        for offer in offers
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
