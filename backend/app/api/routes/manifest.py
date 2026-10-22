"""Manifest-Export -- baut den vollständigen Baum Installation -> Buildings -> Floors -> Rooms
explizit aus ORM-Objekten zusammen (statt impliziter verschachtelter from_attributes-Auflösung),
um die Übersetzung nachvollziehbar und robust zu halten."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.security import require_api_token
from app.manifest.service import ManifestService, NotFoundError
from app.schemas.manifest import (
    BuildingOut,
    BuildingWithFloors,
    FloorOut,
    FloorWithRooms,
    InstallationOut,
    ManifestExport,
    RoomOut,
)

router = APIRouter(dependencies=[Depends(require_api_token)])


@router.get("/manifest", response_model=ManifestExport)
def get_manifest(installation_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        installation = service.get_installation(installation_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    buildings_out: list[BuildingWithFloors] = []
    for building in installation.buildings:
        floors_out: list[FloorWithRooms] = []
        for floor in building.floors:
            rooms_out = [RoomOut.model_validate(r) for r in floor.rooms]
            floors_out.append(
                FloorWithRooms(**FloorOut.model_validate(floor).model_dump(), rooms=rooms_out)
            )
        buildings_out.append(
            BuildingWithFloors(**BuildingOut.model_validate(building).model_dump(), floors=floors_out)
        )

    return ManifestExport(
        installation=InstallationOut.model_validate(installation), buildings=buildings_out
    )
