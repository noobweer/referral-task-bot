from datetime import datetime
from typing import Optional
from ninja import Schema
from pydantic import field_serializer
from typing import Any

class ProfileIn(Schema):
    telegram_id: int
    username: str


class ProfileOut(Schema):
    telegram_id: int
    username: Optional[str] = None
    date_joined_bot: Optional[str] = None
    last_activity: Optional[str] = None
    tasks_done: int = 0
    points: int = 0
    level: int = 0
    
    @field_serializer('date_joined_bot', 'last_activity')
    def serialize_datetime(self, dt: Any):
        if dt is None:
            return None
        # если вдруг уже строка — просто вернем как есть
        if isinstance(dt, str):
            return dt
        # если datetime — форматируем
        return dt.strftime("%d.%m.%Y – %H:%M")