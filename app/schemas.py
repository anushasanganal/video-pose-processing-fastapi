from pydantic import BaseModel

class TaskResponse(BaseModel):
    id: int
    status: str

    class Config:
        from_attributes = True