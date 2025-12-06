from aiogram import Router, F
from bot.config.settings import SUPPORT_USERNAME
from aiogram.types import Message

router = Router()


@router.message(F.text == "💼 Поддержка")
async def show_available_tasks(message: Message):
    text = (
        f"🥰 Если у вас возникли проблемы: @{SUPPORT_USERNAME}"
    )
    await message.answer(text)
