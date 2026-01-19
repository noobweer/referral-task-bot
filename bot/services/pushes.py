import asyncio
import random
import httpx

from bot.config.settings import API_BASE_URL
from bot.api_client.client import fetch_task_details


PUSH_TEMPLATES = [
    "💸 Нужны быстрые бонусы? Не тяни — сделай это задание прямо сейчас:\n\n{task}\n\nЖми «✅ Начать» ниже 👇",
    "⏳ Есть время, но не знаешь чем заняться? Сделай это задание:\n\n{task}\n\nЖми «✅ Начать» ниже 👇",
    "🔥 Напоминание: бонусы сами себя не заработают 😄\nВот задание Level 0:\n\n{task}\n\nЖми «✅ Начать» ниже 👇",
]



def _format_task(task: dict) -> str:
    
    instruction = (task.get("instruction") or "").strip()
    if not instruction:
        instruction = (task.get("description") or "").strip() or "Инструкция скоро появится 🙏"

    text = (
        f"📌 <b>{task['title']}</b>\n\n"
        f"📋 <b>Инструкция:</b>\n{task['instruction']}\n\n"
        f"🎁 Награда: <b>{task['reward']}</b>\n"
    )
    if task.get("link"):
        text += f"\n🔗 <a href='{task['link']}'>Ссылка для выполнения</a>"
    return text


async def fetch_due_pushes(limit: int = 30):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/pushes/due", params={"limit": limit}, timeout=15.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error (pushes/due): {e}")
            return []


async def mark_sent(telegram_id: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/pushes/mark-sent", params={"telegram_id": telegram_id}, timeout=10.0)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"API error (pushes/mark-sent): {e}")
            return False


async def push_worker(bot):
    while True:
        try:
            items = await fetch_due_pushes(limit=30)

            for item in items:
                telegram_id = item.get("telegram_id")
                task = item.get("task")

                # если вдруг заданий level0 нет — просто переносим следующий пуш
                if not task:
                    await mark_sent(telegram_id)
                    continue

                task_id = task.get("id")
                if not task_id:
                    await mark_sent(telegram_id)
                    continue

                full_task = await fetch_task_details(task_id)
                if not full_task:
                    # не смогли получить детали — не шлём пуш, просто отложим на следующий цикл
                    continue

                task_text = _format_task(task)
                template = random.choice(PUSH_TEMPLATES)
                text = template.format(task=task_text)

                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Начать", callback_data=f"start_task:{full_task['id']}")]
                ])

                await bot.send_message(telegram_id, text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=False)
                await mark_sent(telegram_id)

        except Exception as e:
            print("PUSH WORKER ERROR:", e)

        await asyncio.sleep(60)
