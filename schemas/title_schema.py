 
from pydantic import BaseModel

class TitleCreate(BaseModel):
    title: str

    class Config:
        orm_mode = True
