from typing import List
from asgiref.sync import sync_to_async
from django.conf import settings
from api.models import Completed, TelegramUser


def _abs_media(url_path: str | None) -> str | None:
    if not url_path:
        return None
    # url_path уже типа "/media/proof_images/..."
    return f"{settings.PUBLIC_BASE_URL}{url_path}"


@sync_to_async
def get_history(telegram_id: int, limit: int = 10) -> List[Completed]:
    user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return []

    return list(
        Completed.objects
        .select_related("task")
        .filter(user=user)
        .order_by("-id")[:limit]
    )
