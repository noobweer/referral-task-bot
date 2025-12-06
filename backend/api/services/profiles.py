from asgiref.sync import sync_to_async
from api.models import TelegramUser


def _get_profile_telegram(telegram_id: int):
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def get_profile_telegram(telegram_id: int):
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def create_or_update_profile(payload):
    profile_obj, is_created = TelegramUser.objects.update_or_create(
        telegram_id=payload.telegram_id,
        defaults={'username': payload.username}
    )
    return profile_obj, is_created
