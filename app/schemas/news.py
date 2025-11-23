from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    link: str
    description: str | None = None
    published_at: datetime | None = None
    source: str = "vnexpress"
