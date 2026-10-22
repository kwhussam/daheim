"""Pydantic-Schemas für API-I/O und das Installation-Manifest-Aggregat (M1/M2-Umfang)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import DeploymentStatus, NetworkMode, RoomSyncStatus, RoomType


class InstallationCreate(BaseModel):
    network_mode: NetworkMode = NetworkMode.MANAGED


class InstallationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    network_mode: NetworkMode
    deployment_status: DeploymentStatus
    manifest_version: int
    created_at: datetime
    updated_at: datetime


class BuildingCreate(BaseModel):
    installation_id: str
    name: str = Field(min_length=1, max_length=120)
    address: str | None = None


class BuildingUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = None


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    installation_id: str
    name: str
    address: str | None
    created_at: datetime


class FloorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    level: int = 0


class FloorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    building_id: str
    name: str
    level: int
    created_at: datetime


class RoomCreate(BaseModel):
    floor_id: str
    name: str = Field(min_length=1, max_length=120)
    room_type: RoomType = RoomType.OTHER


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    room_type: RoomType | None = None


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    floor_id: str
    name: str
    room_type: RoomType
    ha_area_id: str | None
    sync_status: RoomSyncStatus
    sync_error: str | None
    created_at: datetime


class RoomSyncResult(BaseModel):
    id: str
    ha_area_id: str | None
    sync_status: RoomSyncStatus
    sync_error: str | None = None


class FloorWithRooms(FloorOut):
    rooms: list[RoomOut] = []


class BuildingWithFloors(BuildingOut):
    floors: list[FloorWithRooms] = []


class ManifestExport(BaseModel):
    installation: InstallationOut
    buildings: list[BuildingWithFloors]


class HAHealth(BaseModel):
    reachable: bool
    mode: str
    detail: str | None = None


class HealthStatus(BaseModel):
    status: str
    version: str
    ha_mode: str
    database: str
    home_assistant: HAHealth
