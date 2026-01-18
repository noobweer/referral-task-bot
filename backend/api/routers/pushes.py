from ninja import Router
from ninja.errors import HttpError

from api.models import TelegramUser
from api.services.pushes import locker_passed, get_due_pushes, mark_push_sent

router = Router()


@router.post("/locker-passed")
def post_locker_passed(request, telegram_id: int):
    locker_passed(telegram_id)
    return {"ok": True}


@router.get("/due")
def get_due(request, limit: int = 30):
    return get_due_pushes(limit=limit)


@router.post("/mark-sent")
def post_mark_sent(request, telegram_id: int):
    # если пользователя нет — это ошибка данных
    if not TelegramUser.objects.filter(telegram_id=telegram_id).exists():
        raise HttpError(404, "User not found")
    mark_push_sent(telegram_id)
    return {"ok": True}
