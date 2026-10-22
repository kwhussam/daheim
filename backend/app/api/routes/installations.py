from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.security import require_api_token
from app.manifest.service import ManifestService, NotFoundError
from app.schemas.manifest import InstallationCreate, InstallationOut

router = APIRouter(dependencies=[Depends(require_api_token)])


@router.post("/installations", response_model=InstallationOut, status_code=201)
def create_installation(payload: InstallationCreate, db: Session = Depends(get_db)):
    service = ManifestService(db)
    return service.create_installation(payload.network_mode)


@router.get("/installations/{installation_id}", response_model=InstallationOut)
def get_installation(installation_id: str, db: Session = Depends(get_db)):
    service = ManifestService(db)
    try:
        return service.get_installation(installation_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
