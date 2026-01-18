import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import OuterRef, Exists

from api.models import TelegramUser, Task, Completed


def _pick_random_level0_task_for_user(user: TelegramUser):
    # Берем только level=0, активные, и исключаем уже сделанные/на проверке/в процессе
    completed_qs = Completed.objects.filter(user=user, task=OuterRef("pk")).exclude(
        status=Completed.STATUS_REJECTED  # rejected можно делать снова
    )

    qs = Task.objects.filter(is_active=True, level=0).exclude(Exists(completed_qs))
    tasks = list(qs)
    if not tasks:
        return None
    return random.choice(tasks)


def locker_passed(telegram_id: int):
    user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)

    # ставим только один раз
    if user.locker_passed_at is None:
        user.locker_passed_at = timezone.now()
        user.next_push_at = user.locker_passed_at + timedelta(hours=24)
        user.save(update_fields=["locker_passed_at", "next_push_at"])

    return user


def get_due_pushes(limit: int = 30):
    now = timezone.now()
    users = TelegramUser.objects.filter(
        locker_passed_at__isnull=False,
        next_push_at__isnull=False,
        next_push_at__lte=now,
    ).order_by("next_push_at")[:limit]

    result = []
    for u in users:
        task = _pick_random_level0_task_for_user(u)
        result.append(
            {
                "telegram_id": u.telegram_id,
                "task": None
                if task is None
                else {
                    "id": task.id,
                    "title": task.title,
                    "instruction": task.instruction,
                    "link": task.link,
                    "reward": task.reward,
                },
            }
        )
    return result


def mark_push_sent(telegram_id: int):
    # после пуша — следующий через 72 часа
    now = timezone.now()
    TelegramUser.objects.filter(telegram_id=telegram_id).update(
        next_push_at=now + timedelta(hours=72)
    )
