from aiogram import Router, F
from bot.api_client.client import fetch_profile
from aiogram.types import Message

router = Router()


@router.message(F.text == "👤 Профиль")
async def show_available_tasks(message: Message):
    telegram_id = message.from_user.id
    profile = await fetch_profile(telegram_id)
    text = (
        f"📌 Профиль пользователя: <b>{profile['username']}</b>\n\n"
        
        f"Регистрация: <b>{profile['date_joined_bot']}</b>\n"
        f"Последняя активность: <b>{profile['last_activity']}</b>\n\n"
        f"Заданий выполнено: <b>{profile['tasks_done']}</b>"
    )
    await message.answer(text, parse_mode="HTML")
