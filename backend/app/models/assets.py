from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Index

from enum import Enum

class ResourceType(str, Enum):
    type = "type"
    character = "character"
    corporation = "corporation"
    alliance = "alliance"

class ImageCache(SQLModel, table=True):
    __tablename__ = "image_cache"
    # Composite Index for fast lookups
    __table_args__ = (
        Index("idx_resource_variant", "resource_type", "resource_id", "variant"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    resource_type: ResourceType = Field(index=True)
    resource_id: int = Field(index=True)
    variant: str = Field(default="icon", index=True) # icon, portrait, logo
    
    # Store binary data
    blob_data: bytes

    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
