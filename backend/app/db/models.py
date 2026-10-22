"""ORM-Modelle des Installation Manifest (M2-Umfang: Installation/Building/Floor/Room).

Residents, Sensoren/Geräte, Szenarien und Automationsparameter sind gemäß
docs/IMPLEMENTATION_PLAN.md bewusst erst ab M3/M4/M5 vorgesehen und hier noch nicht modelliert.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class NetworkMode(str, enum.Enum):
    MANAGED = "managed"
    CUSTOMER = "customer"
    HYBRID = "hybrid"


class DeploymentStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURING = "configuring"
    APPLIED = "applied"
    FAILED = "failed"


class RoomType(str, enum.Enum):
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    HALLWAY = "hallway"
    OFFICE = "office"
    OTHER = "other"


class RoomSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    NOT_SUPPORTED = "not_supported"


class Installation(Base):
    """Wurzel-Entität des Installation Manifest. manifest_version steigt monoton bei jeder
    strukturellen Änderung (siehe ManifestService)."""

    __tablename__ = "installations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    network_mode: Mapped[NetworkMode] = mapped_column(
        SAEnum(NetworkMode), default=NetworkMode.MANAGED, nullable=False
    )
    deployment_status: Mapped[DeploymentStatus] = mapped_column(
        SAEnum(DeploymentStatus), default=DeploymentStatus.DRAFT, nullable=False
    )
    manifest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    buildings: Mapped[list["Building"]] = relationship(
        back_populates="installation", cascade="all, delete-orphan"
    )

    def bump_version(self) -> None:
        self.manifest_version += 1
        self.updated_at = _now()


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (UniqueConstraint("installation_id", "name", name="uq_building_installation_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    installation_id: Mapped[str] = mapped_column(ForeignKey("installations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    installation: Mapped[Installation] = relationship(back_populates="buildings")
    floors: Mapped[list["Floor"]] = relationship(back_populates="building", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("building_id", "name", name="uq_floor_building_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    building: Mapped[Building] = relationship(back_populates="floors")
    rooms: Mapped[list["Room"]] = relationship(back_populates="floor", cascade="all, delete-orphan")


class Room(Base):
    """Ein Raum wird intern über eine stabile UUID identifiziert, niemals über eine
    IP-Adresse. ha_area_id/sync_status sind reine Sync-Artefakte des Best-Effort-HA-Abgleichs
    (siehe docs/ARCHITECTURE.md Abschnitt 4) -- das Manifest bleibt die autoritative Quelle."""

    __tablename__ = "rooms"
    __table_args__ = (UniqueConstraint("floor_id", "name", name="uq_room_floor_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    room_type: Mapped[RoomType] = mapped_column(SAEnum(RoomType), default=RoomType.OTHER, nullable=False)
    ha_area_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sync_status: Mapped[RoomSyncStatus] = mapped_column(
        SAEnum(RoomSyncStatus), default=RoomSyncStatus.PENDING, nullable=False
    )
    sync_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    floor: Mapped[Floor] = relationship(back_populates="rooms")
