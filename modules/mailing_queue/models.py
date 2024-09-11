from typing import Optional

from pydantic import BaseModel


class MailingModel(BaseModel):
    chat_id: int
    content: str
    media_type: Optional[str] = None  # 'photo', 'video', 'document', or None
    media_id: Optional[str] = None  # File ID of the media
