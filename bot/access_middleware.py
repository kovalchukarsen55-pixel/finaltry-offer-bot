"""Restrict access to partners + admins."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from bot import sheets
from bot.config import settings


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        
        user = getattr(event, "from_user", None)
        user_id = getattr(user, "id", None)
        if user_id is None:
            
            return

        # Админам всегда можно
        if user_id in settings.admin_ids:
            return await handler(event, data)

        # Партнёры из sheets (пока заглушка, но оставим на будущее)
        partners = await sheets.partner_ids()  
        if user_id not in partners:
            if isinstance(event, Message):
                await event.answer("⛔ Нет доступа. Обратитесь к администратору.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Нет доступа", show_alert=True)
            return  # drop update

        return await handler(event, data)
