from aiogram import Router, F
from bot.config.settings import SUPPORT_USERNAME
from bot.utils.subscription import ensure_subscribed_message
from aiogram.types import Message

router = Router()


@router.message(F.text == "💼 Поддержка")
async def show_available_tasks(message: Message):
    # 🔒 Проверяем подписку
    if not await ensure_subscribed_message(message):
        return
    text = (
        f"🥰 Если у вас возникли проблемы: @{SUPPORT_USERNAME}"
    )
    await message.answer(text)
