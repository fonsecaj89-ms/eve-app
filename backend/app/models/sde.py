"""
SQLModel ORM mappings for Fuzzwork SDE schema.

These models map to existing tables created by the Fuzzwork PostgreSQL dump.
They are read-only reference data for the EVE Online universe.

Note: Fuzzwork uses legacy camelCase column names, so we need to map them
using Field(sa_column_kwargs={'name': 'actualColumnName'})
"""

from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from datetime import datetime


class InvType(SQLModel, table=True):
    """
    Maps to invTypes table - All items, ships, modules, etc. in EVE Online.
    """
    __tablename__ = "invTypes"
    
    type_id: int = Field(
        sa_column_kwargs={"name": "typeID"},
        primary_key=True
    )
    type_name: str = Field(
        sa_column_kwargs={"name": "typeName"},
        index=True
    )
    description: Optional[str] = Field(default=None)
    volume: Optional[float] = Field(default=None)
    portion_size: Optional[int] = Field(
        sa_column_kwargs={"name": "portionSize"},
        default=1
    )
    market_group_id: Optional[int] = Field(
        sa_column_kwargs={"name": "marketGroupID"},
        default=None,
        foreign_key="invMarketGroups.marketGroupID"
    )
    group_id: Optional[int] = Field(
        sa_column_kwargs={"name": "groupID"},
        default=None
    )
    published: Optional[bool] = Field(default=None)
    
    # Relationship to market group
    # market_group: Optional["InvMarketGroup"] = Relationship(back_populates="types")


class MapSolarSystem(SQLModel, table=True):
    """
    Maps to mapSolarSystems table - All solar systems in EVE.
    """
    __tablename__ = "mapSolarSystems"
    
    solar_system_id: int = Field(
        sa_column_kwargs={"name": "solarSystemID"},
        primary_key=True
    )
    solar_system_name: str = Field(
        sa_column_kwargs={"name": "solarSystemName"},
        index=True
    )
    region_id: Optional[int] = Field(
        sa_column_kwargs={"name": "regionID"},
        default=None
    )
    constellation_id: Optional[int] = Field(
        sa_column_kwargs={"name": "constellationID"},
        default=None
    )
    security: Optional[float] = Field(default=None)
    x: Optional[float] = Field(default=None)
    y: Optional[float] = Field(default=None)
    z: Optional[float] = Field(default=None)
    
    @property
    def security_status(self) -> str:
        """Returns 'highsec', 'lowsec', or 'nullsec' based on security rating."""
        if self.security is None:
            return "unknown"
        if self.security >= 0.5:
            return "highsec"
        elif self.security > 0.0:
            return "lowsec"
        else:
            return "nullsec"


class MapRegion(SQLModel, table=True):
    """
    Maps to mapRegions table - All regions in EVE.
    """
    __tablename__ = "mapRegions"
    
    region_id: int = Field(
        sa_column_kwargs={"name": "regionID"},
        primary_key=True
    )
    region_name: str = Field(
        sa_column_kwargs={"name": "regionName"},
        index=True
    )


class StaStation(SQLModel, table=True):
    """
    Maps to staStations table - NPC stations (not player structures).
    """
    __tablename__ = "staStations"
    
    station_id: int = Field(
        sa_column_kwargs={"name": "stationID"},
        primary_key=True
    )
    station_name: str = Field(
        sa_column_kwargs={"name": "stationName"},
        index=True
    )
    solar_system_id: Optional[int] = Field(
        sa_column_kwargs={"name": "solarSystemID"},
        default=None,
        foreign_key="mapSolarSystems.solarSystemID"
    )
    station_type_id: Optional[int] = Field(
        sa_column_kwargs={"name": "stationTypeID"},
        default=None
    )
    reprocessing_efficiency: Optional[float] = Field(
        sa_column_kwargs={"name": "reprocessingEfficiency"},
        default=0.5
    )
    reprocessing_stations_take: Optional[float] = Field(
        sa_column_kwargs={"name": "reprocessingStationsTake"},
        default=0.05
    )


class IndustryActivityMaterial(SQLModel, table=True):
    """
    Maps to industryActivityMaterials table - Blueprint material requirements.
    """
    __tablename__ = "industryActivityMaterials"
    
    type_id: int = Field(
        sa_column_kwargs={"name": "typeID"},
        primary_key=True,
        foreign_key="invTypes.typeID"
    )
    activity_id: int = Field(
        sa_column_kwargs={"name": "activityID"},
        primary_key=True
    )
    material_type_id: int = Field(
        sa_column_kwargs={"name": "materialTypeID"},
        primary_key=True,
        foreign_key="invTypes.typeID"
    )
    quantity: int = Field(default=1)


class InvMarketGroup(SQLModel, table=True):
    """
    Maps to invMarketGroups table - Market category tree structure.
    """
    __tablename__ = "invMarketGroups"
    
    market_group_id: int = Field(
        sa_column_kwargs={"name": "marketGroupID"},
        primary_key=True
    )
    parent_group_id: Optional[int] = Field(
        sa_column_kwargs={"name": "parentGroupID"},
        default=None,
        foreign_key="invMarketGroups.marketGroupID"
    )
    market_group_name: str = Field(
        sa_column_kwargs={"name": "marketGroupName"},
        index=True
    )
    description: Optional[str] = Field(default=None)
    icon_id: Optional[int] = Field(
        sa_column_kwargs={"name": "iconID"},
        default=None
    )
    has_types: Optional[bool] = Field(
        sa_column_kwargs={"name": "hasTypes"},
        default=True
    )
    
    # Self-referential relationship for tree structure
    # parent: Optional["InvMarketGroup"] = Relationship(
    #     sa_relationship_kwargs={"remote_side": "InvMarketGroup.market_group_id"}
    # )
    # children: list["InvMarketGroup"] = Relationship(back_populates="parent")
    # types: list["InvType"] = Relationship(back_populates="market_group")


class MapSolarSystemJump(SQLModel, table=True):
    """
    Maps to mapSolarSystemJumps table - Stargate connections between systems.
    """
    __tablename__ = "mapSolarSystemJumps"
    
    from_solar_system_id: int = Field(
        sa_column_kwargs={"name": "fromSolarSystemID"},
        primary_key=True,
        foreign_key="mapSolarSystems.solarSystemID"
    )
    to_solar_system_id: int = Field(
        sa_column_kwargs={"name": "toSolarSystemID"},
        primary_key=True,
        foreign_key="mapSolarSystems.solarSystemID"
    )
