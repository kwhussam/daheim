from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.security import require_api_token
from app.manifest.service import DuplicateNameError, ManifestService, NotFoundError
from app.schemas.manifest import BuildingCreate, BuildingOut, BuildingUpdate, FloorCreate, FloorOut

router = APIRouter(dependencies=[Depends(require_api_token)])


@router.post("/buildings", response_model=BuildingOut, status_code=201)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.create_building(payload.installation_id, payload.name, payload.address)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/buildings", response_model=list[BuildingOut])
def list_buildings(installation_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    return service.list_buildings(installation_id)


@router.patch("/buildings/{building_id}", response_model=BuildingOut)
def update_building(building_id: str, payload: BuildingUpdate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.update_building(building_id, payload.name, payload.address)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/buildings/{building_id}", status_code=204)
def delete_building(building_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        service.delete_building(building_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/buildings/{building_id}/floors", response_model=FloorOut, status_code=201)
def create_floor(building_id: str, payload: FloorCreate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.create_floor(building_id, payload.name, payload.level)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/buildings/{building_id}/floors", response_model=list[FloorOut])
def list_floors(building_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    return service.list_floors(building_id)
