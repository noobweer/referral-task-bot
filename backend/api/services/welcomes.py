from api.models import WelcomeMessage
from asgiref.sync import sync_to_async


@sync_to_async
def get_welcome_messages():
    return list(WelcomeMessage.objects.filter(is_active=True))
