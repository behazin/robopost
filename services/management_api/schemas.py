from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class SourceBase(BaseModel):
    name: str


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class DestinationBase(BaseModel):
    name: str
    credentials: Dict[str, Any]


class DestinationCreate(DestinationBase):
    pass


class Destination(DestinationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
