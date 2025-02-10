from pydantic import BaseModel


class prop(BaseModel):
    location: str
    area: str
    description: str