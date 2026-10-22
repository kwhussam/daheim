"""ManifestService -- idempotente Business-Logik für das Installation Manifest.

Jede strukturelle Schreiboperation erhöht Installation.manifest_version. Der Best-Effort-HA-
Sync (sync_room_to_ha) wirft niemals wegen eines HA-Fehlers -- das Manifest bleibt die
autoritative Quelle, unabhängig vom HA-Status (siehe docs/ARCHITECTURE.md Abschnitt 4).
"""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Building,
    Floor,
    Installation,
    NetworkMode,
    Room,
    RoomSyncStatus,
    RoomType,
)
from app.ha_client.base import HomeAssistantClient
from app.ha_client.exceptions import AreaRegistryUnsupportedError, HomeAssistantUnavailableError


class DuplicateNameError(Exception):
    """Eine Namensgleichheit verletzt eine Eindeutigkeits-Regel (z. B. doppelter Raum)."""


class NotFoundError(Exception):
    """Die angeforderte Manifest-Entität existiert nicht."""


class ManifestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Installation ---
    def create_installation(self, network_mode: NetworkMode) -> Installation:
        installation = Installation(network_mode=network_mode)
        self.db.add(installation)
        self.db.commit()
        self.db.refresh(installation)
        return installation

    def get_installation(self, installation_id: str) -> Installation:
        installation = self.db.get(Installation, installation_id)
        if installation is None:
            raise NotFoundError(f"Installation {installation_id} not found")
        return installation

    # --- Building ---
    def create_building(self, installation_id: str, name: str, address: str | None) -> Building:
        installation = self.get_installation(installation_id)
        building = Building(installation_id=installation.id, name=name, address=address)
        self.db.add(building)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateNameError(
                f"Building '{name}' already exists for this installation."
            ) from exc
        installation.bump_version()
        self.db.commit()
        self.db.refresh(building)
        return building

    def get_building(self, building_id: str) -> Building:
        building = self.db.get(Building, building_id)
        if building is None:
            raise NotFoundError(f"Building {building_id} not found")
        return building

    def list_buildings(self, installation_id: str) -> list[Building]:
        return (
            self.db.query(Building)
            .filter(Building.installation_id == installation_id)
            .order_by(Building.created_at)
            .all()
        )

    def update_building(self, building_id: str, name: str | None, address: str | None) -> Building:
        building = self.get_building(building_id)
        if name is not None:
            building.name = name
        if address is not None:
            building.address = address
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateNameError(f"Building name '{name}' already in use.") from exc
        building.installation.bump_version()
        self.db.commit()
        self.db.refresh(building)
        return building

    def delete_building(self, building_id: str) -> None:
        building = self.get_building(building_id)
        installation = building.installation
        self.db.delete(building)
        installation.bump_version()
        self.db.commit()

    # --- Floor ---
    def create_floor(self, building_id: str, name: str, level: int) -> Floor:
        building = self.get_building(building_id)
        floor = Floor(building_id=building.id, name=name, level=level)
        self.db.add(floor)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateNameError(f"Floor '{name}' already exists for this building.") from exc
        building.installation.bump_version()
        self.db.commit()
        self.db.refresh(floor)
        return floor

    def get_floor(self, floor_id: str) -> Floor:
        floor = self.db.get(Floor, floor_id)
        if floor is None:
            raise NotFoundError(f"Floor {floor_id} not found")
        return floor

    def list_floors(self, building_id: str) -> list[Floor]:
        return (
            self.db.query(Floor)
            .filter(Floor.building_id == building_id)
            .order_by(Floor.level, Floor.created_at)
            .all()
        )

    # --- Room ---
    def create_room(self, floor_id: str, name: str, room_type: RoomType) -> Room:
        floor = self.get_floor(floor_id)
        room = Room(floor_id=floor.id, name=name, room_type=room_type)
        self.db.add(room)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateNameError(f"Room '{name}' already exists on this floor.") from exc
        floor.building.installation.bump_version()
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_room(self, room_id: str) -> Room:
        room = self.db.get(Room, room_id)
        if room is None:
            raise NotFoundError(f"Room {room_id} not found")
        return room

    def list_rooms(self, floor_id: str) -> list[Room]:
        return self.db.query(Room).filter(Room.floor_id == floor_id).order_by(Room.created_at).all()

    def update_room(self, room_id: str, name: str | None, room_type: RoomType | None) -> Room:
        room = self.get_room(room_id)
        if name is not None:
            room.name = name
        if room_type is not None:
            room.room_type = room_type
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateNameError(f"Room name '{name}' already in use on this floor.") from exc
        room.floor.building.installation.bump_version()
        self.db.commit()
        self.db.refresh(room)
        return room

    def delete_room(self, room_id: str) -> None:
        room = self.get_room(room_id)
        installation = room.floor.building.installation
        self.db.delete(room)
        installation.bump_version()
        self.db.commit()

    # --- Best-Effort HA-Sync (Soll-Ist-Abgleich für Räume) ---
    async def sync_room_to_ha(self, room_id: str, ha_client: HomeAssistantClient) -> Room:
        room = self.get_room(room_id)
        try:
            area = await ha_client.get_or_create_area(room.name)
            room.ha_area_id = area["area_id"]
            room.sync_status = RoomSyncStatus.SYNCED
            room.sync_error = None
        except (HomeAssistantUnavailableError, AreaRegistryUnsupportedError) as exc:
            room.sync_status = RoomSyncStatus.FAILED
            room.sync_error = str(exc)
        self.db.commit()
        self.db.refresh(room)
        return room
