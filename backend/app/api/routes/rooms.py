from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_ha_client
from app.api.security import require_api_token
from app.manifest.service import DuplicateNameError, ManifestService, NotFoundError
from app.schemas.manifest import RoomCreate, RoomOut, RoomSyncResult, RoomUpdate

router = APIRouter(dependencies=[Depends(require_api_token)])


@router.post("/rooms", response_model=RoomOut, status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.create_room(payload.floor_id, payload.name, payload.room_type)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(floor_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    return service.list_rooms(floor_id)


@router.patch("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: str, payload: RoomUpdate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.update_room(room_id, payload.name, payload.room_type)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        service.delete_room(room_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rooms/{room_id}/sync", response_model=RoomSyncResult)
async def sync_room(room_id: str, db: Session = Depends(get_db), ha_client=Depends(get_ha_client)):
    service = ManifestService(db)
    try:
        room = await service.sync_room_to_ha(room_id, ha_client)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RoomSyncResult(
        id=room.id,
        ha_area_id=room.ha_area_id,
        sync_status=room.sync_status,
        sync_error=room.sync_error,
    )
