from typing import Optional, Dict, List, Any
from sqlmodel import Field, SQLModel, Column, JSON
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(index=True, unique=True)
    character_name: str
    
    # Store settings as JSON
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Store saved routes as structured JSON
    saved_routes: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
