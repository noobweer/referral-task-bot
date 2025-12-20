from typing import List
from ninja import Router
from django.conf import settings

from api.models import Completed
from ..schemas.history import HistoryItemOut
from ..services.history import get_history

router = Router()


def _status_label(code: str) -> str:
    return {
        Completed.STATUS_PENDING: "В процессе",
        Completed.STATUS_REVIEW: "На проверке",
        Completed.STATUS_DONE: "Принято",
        Completed.STATUS_REJECTED: "Отклонено",
    }.get(code, code)


def _serialize_completed(c: Completed) -> HistoryItemOut:
    proof_image_url = None
    if getattr(c, "proof_image", None):
        proof_image_url = f"{settings.PUBLIC_BASE_URL}{c.proof_image.url}"

    return HistoryItemOut(
        task_id=c.task_id,
        title=c.task.title,
        reward=int(c.task.reward or 0),
        status=c.status,
        status_label=_status_label(c.status),
        proof_text=c.proof_text or None,
        proof_image=proof_image_url,
        admin_comment=c.admin_comment or None,
    )


@router.get("/", response=List[HistoryItemOut])
async def history(request, telegram_id: int, limit: int = 10):
    items = await get_history(telegram_id, limit=limit)
    return [_serialize_completed(c) for c in items]
