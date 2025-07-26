import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN
from handlers import default
from aggregator import start_aggregator
import aiohttp

async def main():
    bot = Bot(token=API_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(default.router)

    # запускаем агрегатор как фоновую задачу
    session = aiohttp.ClientSession()
    asyncio.create_task(start_aggregator(session, bot))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
