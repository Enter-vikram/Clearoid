# schemas/title_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TitleCreate(BaseModel):
    title: str

    model_config = {
        "from_attributes": True
    }

class TitleUpdate(BaseModel):
    title: Optional[str] = None
    normalized_title: Optional[str] = None
    is_duplicate: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class TitleOut(BaseModel):
    id: int
    title: str
    normalized_title: str
    is_duplicate: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
