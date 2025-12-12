from ninja import Router
from ..schemas.profiles import ProfileIn, ProfileOut
from ..services.profiles import get_profile_telegram, create_or_update_profile

router = Router()


@router.get("/profiles/{telegram_id}", response=ProfileOut)
def get_profile(request, telegram_id: int):
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        raise HttpError(404, "Profile not found")


@router.post('/', response={201: ProfileOut, 200: ProfileOut})
async def post_profile(request, payload: ProfileIn):
    profile, is_created = await create_or_update_profile(payload)
    status_code = 201 if is_created else 200
    return status_code, profile
