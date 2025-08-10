import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from loguru import logger

from bot.config import settings
from bot.handlers import router
from bot.access_middleware import AccessMiddleware 

async def main():
    logger.info("Bootstrapping bot...")
    bot = Bot(token=settings.bot_token, default_parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    access = AccessMiddleware()
    dp.message.middleware(access)
    dp.callback_query.middleware(access)

    dp.include_router(router)

    logger.info("Starting polling…")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )

if __name__ == "__main__":
    try:
        print("🤖 Bot started!")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
