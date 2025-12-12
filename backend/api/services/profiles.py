from asgiref.sync import sync_to_async
from api.models import TelegramUser

WELCOME_BONUS = 300

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
    
    if is_created and not profile_obj.bonus_claimed:
        profile_obj.points += WELCOME_BONUS
        profile_obj.bonus_claimed = True
        profile_obj.save(update_fields=["points", "bonus_claimed"])

    return profile_obj, is_created