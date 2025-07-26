from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Привет! Используй /filter, чтобы задать пороги.")
