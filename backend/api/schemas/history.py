from typing import Optional
from ninja import Schema


class HistoryItemOut(Schema):
    task_id: int
    title: str
    reward: int
    status: str           # "PE" / "RV" / "DN" / "RJ"
    status_label: str     # "В процессе" / ...
    proof_text: Optional[str] = None
    proof_image: Optional[str] = None   # абсолютный URL или None
    admin_comment: Optional[str] = None
