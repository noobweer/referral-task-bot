from ninja import Router
from typing import List
from ..schemas.welcomes import WelcomeOut
from ..services.welcomes import get_welcome_messages

router = Router()


@router.get('/', response=List[WelcomeOut])
async def get_messages(request):
    return await get_welcome_messages()
