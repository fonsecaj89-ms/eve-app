from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Index

class MarketOrder(SQLModel, table=True):
    __tablename__ = "market_orders"
    __table_args__ = (
        Index("idx_region_type", "region_id", "type_id"),
        Index("idx_location", "location_id"),
    )

    order_id: int = Field(primary_key=True)
    type_id: int = Field(index=True)
    location_id: int = Field(index=True)
    region_id: int = Field(index=True)
    system_id: int = Field(index=True)
    
    is_buy_order: bool
    price: float
    volume_remain: int
    volume_total: int
    min_volume: int
    
    issued: datetime
    duration: int
    range: str # station, region, solarsystem, 1, 2, ...
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
