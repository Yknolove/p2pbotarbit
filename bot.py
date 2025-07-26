
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Import handlers to register them
import handlers.default

if __name__ == "__main__":
    dp.run_polling(bot)
