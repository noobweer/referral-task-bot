import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.settings import BOT_TOKEN
from handlers.start import router as start_router
from handlers.profile import router as profile_router
from handlers.support import router as support_router
from handlers.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(support_router)
dp.include_router(tasks_router)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
