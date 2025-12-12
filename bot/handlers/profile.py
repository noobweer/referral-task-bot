from aiogram import Router, F
from bot.api_client.client import fetch_profile
from aiogram.types import Message
from bot.utils.subscription import ensure_subscribed_message

router = Router()


@router.message(F.text == "👤 Профиль")
async def show_available_tasks(message: Message):
    # 🔒 Проверяем подписку
    if not await ensure_subscribed_message(message):
        return
    telegram_id = message.from_user.id
    profile = await fetch_profile(telegram_id)

    if not profile:
        await message.answer("Профиль временно недоступен. Попробуй ещё раз через минуту 🙏")
        return

    username = profile.get("username") or "—"
    points = profile.get("points", 0)
    tasks_done = profile.get("tasks_done", 0)
    date_joined = profile.get("date_joined_bot", "")
    last_activity = profile.get("last_activity", "")

    await message.answer(
        f"📌 Профиль пользователя: <b>{username}</b>\n\n"
        f"🪙 Баланс: <b>{points}</b> баллов\n"
        f"✅ Выполнено заданий: <b>{tasks_done}</b>\n",
        parse_mode="HTML"
    )
