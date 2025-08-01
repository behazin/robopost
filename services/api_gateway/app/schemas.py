from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
import enum

class Platform(str, enum.Enum):
    TELEGRAM = "TELEGRAM"
    WORDPRESS = "WORDPRESS"
    INSTAGRAM = "INSTAGRAM"
    TWITTER = "TWITTER"

# --- Source Schemas ---
class SourceBase(BaseModel):
    name: str = Field(..., max_length=255)
    url: HttpUrl

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    id: int

    class Config:
        orm_mode = True

# --- Destination Schemas ---
class DestinationBase(BaseModel):
    name: str = Field(..., max_length=255)
    platform: Platform
    credentials: Dict[str, Any]
    rate_limit_per_minute: Optional[int] = None

class DestinationCreate(DestinationBase):
    pass

class Destination(DestinationBase):
    id: int

    class Config:
        orm_mode = True

# --- Admin Schemas ---
class AdminBase(BaseModel):
    name: str = Field(..., max_length=255)
    telegram_id: str = Field(..., max_length=255)

class AdminCreate(AdminBase):
    pass

class Admin(AdminBase):
    id: int

    class Config:
        orm_mode = True

# --- Mapping Schemas ---
class SourceDestinationMap(BaseModel):
    source_id: int
    destination_id: int
    enabled: bool

    class Config:
        orm_mode = True

class AdminDestinationMap(BaseModel):
    admin_id: int
    destination_id: int

    class Config:
        orm_mode = True

class LinkToggle(BaseModel):
    enabled: bool