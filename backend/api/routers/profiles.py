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


def _fmt_dt(dt):
    if not dt:
        return None
    return dt.strftime("%d.%m.%Y – %H:%M")


@router.post('/', response={201: ProfileOut, 200: ProfileOut})
async def post_profile(request, payload: ProfileIn):
    profile, is_created = await create_or_update_profile(payload)
    status_code = 201 if is_created else 200
    return status_code, profile


@router.get("/{telegram_id}", response=ProfileOut)
async def get_profile(request, telegram_id: int):
    profile = await get_profile_telegram(telegram_id)

    return {
        "telegram_id": profile.telegram_id,
        "username": profile.username,
        "date_joined_bot": _fmt_dt(profile.date_joined_bot),
        "last_activity": _fmt_dt(profile.last_activity),
        "tasks_done": profile.tasks_done,
        "points": profile.points,
        "level": calc_level(profile.tasks_done or 0),
    }
