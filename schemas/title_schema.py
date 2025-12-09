from pydantic import BaseModel

class TitleCreate(BaseModel):
    title: str

    model_config = {
        "from_attributes": True
    }
