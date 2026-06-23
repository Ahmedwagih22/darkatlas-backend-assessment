from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.session import get_db
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate, AssetWithRelations, PaginatedAssets
from app.services import asset_service

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/", response_model=AssetOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    asset = asset_service.create_asset(db, data)
    return asset_service._to_out(asset)


@router.get("/", response_model=PaginatedAssets)
def list_assets(
    type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    value_contains: Optional[str] = None,
    sort_by: str = Query("last_seen", pattern="^(last_seen|first_seen|value|type|status)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, items = asset_service.list_assets(
        db, type=type, status=status, tag=tag, value_contains=value_contains,
        sort_by=sort_by, sort_dir=sort_dir, page=page, page_size=page_size,
    )
    return PaginatedAssets(total=total, page=page, page_size=page_size, items=[asset_service._to_out(a) for a in items])


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_service._to_out(asset)


@router.get("/{asset_id}/graph", response_model=AssetWithRelations)
def get_asset_graph(asset_id: UUID, db: Session = Depends(get_db)):
    result = asset_service.get_asset_with_relations(db, asset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Asset not found")
    return result


@router.patch("/{asset_id}", response_model=AssetOut, dependencies=[Depends(require_api_key)])
def update_asset(asset_id: UUID, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = asset_service.update_asset(db, asset_id, data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_service._to_out(asset)


@router.post("/{asset_id}/stale", response_model=AssetOut, dependencies=[Depends(require_api_key)])
def mark_stale(asset_id: UUID, db: Session = Depends(get_db)):
    asset = asset_service.mark_stale(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_service._to_out(asset)


@router.delete("/{asset_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_asset(asset_id: UUID, db: Session = Depends(get_db)):
    if not asset_service.delete_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Asset not found")
