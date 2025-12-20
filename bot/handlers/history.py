from aiogram import Router, F
from aiogram.types import Message
from bot.utils.subscription import ensure_subscribed_message
from bot.api_client.client import fetch_history

router = Router()


@router.message(F.text == "📜 История")
async def show_history(message: Message):
    if not await ensure_subscribed_message(message):
        return

    telegram_id = message.from_user.id
    items = await fetch_history(telegram_id, limit=15)

    if not items:
        await message.answer("📜 История пуста. Выполни первое задание 🙂")
        return

    lines = ["📜 <b>История заданий</b>\n"]

    for i, x in enumerate(items, start=1):
        proof = []
        if x.get("proof_text"):
            proof.append("текст")
        if x.get("proof_image"):
            proof.append("фото")
        proof_str = f" (пруф: {', '.join(proof)})" if proof else ""

        line = (
            f"{i}) <b>{x.get('title','—')}</b>\n"
            f"   Статус: <b>{x.get('status_label','—')}</b>{proof_str}\n"
            f"   Награда: <b>{x.get('reward',0)}</b> баллов"
        )

        admin_comment = x.get("admin_comment")
        if admin_comment:
            line += f"\n   💬 Коммент админа: <i>{admin_comment}</i>"

        lines.append(line)

    await message.answer("\n\n".join(lines), parse_mode="HTML")
