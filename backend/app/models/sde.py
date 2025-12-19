from typing import Optional
from sqlmodel import Field, SQLModel

class InvType(SQLModel, table=True):
    __tablename__ = "invTypes"
    typeID: int = Field(primary_key=True)
    groupID: Optional[int] = Field(default=None, index=True)
    typeName: str = Field(index=True)
    description: Optional[str] = None
    mass: Optional[float] = None
    volume: Optional[float] = None
    capacity: Optional[float] = None
    portionSize: Optional[int] = None
    raceID: Optional[int] = None
    basePrice: Optional[float] = None
    published: bool = Field(default=True)
    marketGroupID: Optional[int] = Field(default=None, index=True)
    iconID: Optional[int] = None
    soundID: Optional[int] = None
    graphicID: Optional[int] = None

class MapRegion(SQLModel, table=True):
    __tablename__ = "mapRegions"
    regionID: int = Field(primary_key=True)
    regionName: str = Field(index=True)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    xMin: Optional[float] = None
    xMax: Optional[float] = None
    yMin: Optional[float] = None
    yMax: Optional[float] = None
    zMin: Optional[float] = None
    zMax: Optional[float] = None
    factionID: Optional[int] = None
    radius: Optional[float] = None

class MapSolarSystem(SQLModel, table=True):
    __tablename__ = "mapSolarSystems"
    solarSystemID: int = Field(primary_key=True)
    regionID: int = Field(foreign_key="mapRegions.regionID", index=True)
    constellationID: int = Field(index=True)
    solarSystemName: str = Field(index=True)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    xMin: Optional[float] = None
    xMax: Optional[float] = None
    yMin: Optional[float] = None
    yMax: Optional[float] = None
    zMin: Optional[float] = None
    zMax: Optional[float] = None
    luminosity: Optional[float] = None
    border: Optional[bool] = None
    fringe: Optional[bool] = None
    corridor: Optional[bool] = None
    hub: Optional[bool] = None
    international: Optional[bool] = None
    regional: Optional[bool] = None
    constellation: Optional[str] = None # Sometimes denormalized
    security: Optional[float] = None
    factionID: Optional[int] = None
    radius: Optional[float] = None
    sunTypeID: Optional[int] = None
    securityClass: Optional[str] = None

class StaStation(SQLModel, table=True):
    __tablename__ = "staStations"
    stationID: int = Field(primary_key=True)
    security: Optional[float] = None # Note: Fuzzwork dump might differ in schema nuances
    dockingCostPerVolume: Optional[float] = None
    maxShipVolumeDockable: Optional[float] = None
    officeRentalCost: Optional[int] = None
    operationID: Optional[int] = None
    stationTypeID: Optional[int] = None
    corporationID: Optional[int] = None
    solarSystemID: Optional[int] = Field(foreign_key="mapSolarSystems.solarSystemID", index=True)
    constellationID: Optional[int] = None
    regionID: Optional[int] = None
    stationName: str = Field(index=True)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    reprocessingEfficiency: Optional[float] = None
    reprocessingStationsTake: Optional[float] = None
    reprocessingHangarFlag: Optional[int] = None

class MapSolarSystemJumps(SQLModel, table=True):
    __tablename__ = "mapSolarSystemJumps"
    fromRegionID: Optional[int] = None
    fromConstellationID: Optional[int] = None
    fromSolarSystemID: int = Field(primary_key=True)
    toSolarSystemID: int = Field(primary_key=True)
    toConstellationID: Optional[int] = None
    toRegionID: Optional[int] = None

