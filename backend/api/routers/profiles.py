from ninja import Router
from ..schemas.profiles import ProfileIn, ProfileOut
from ..services.profiles import get_profile_telegram, create_or_update_profile

router = Router()

def calc_level(tasks_done: int) -> int:
    if tasks_done >= 30:
        return 3
    if tasks_done >= 15:
        return 2
    if tasks_done >= 5:
        return 1
    return 0

@router.get("/{telegram_id}", response=ProfileOut)
def get_profile(request, telegram_id: int):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        raise HttpError(404, "Profile not found")

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "date_joined_bot": user.date_joined_bot,
        "last_activity": user.last_activity,
        "tasks_done": user.tasks_done,
        "points": user.points,
        "level": calc_level(user.tasks_done or 0),
    }



@router.post('/', response={201: ProfileOut, 200: ProfileOut})
async def post_profile(request, payload: ProfileIn):
    profile, is_created = await create_or_update_profile(payload)
    status_code = 201 if is_created else 200
    return status_code, profile
