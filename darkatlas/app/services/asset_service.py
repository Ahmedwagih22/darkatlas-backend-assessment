from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, func, String
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetStatus
from app.models.relationship import AssetRelationship
from app.schemas.asset import AssetCreate, AssetUpdate, AssetWithRelations, AssetOut, RelatedAsset


def create_asset(db: Session, data: AssetCreate) -> Asset:
    now = datetime.now(timezone.utc)
    asset = Asset(
        type=data.type,
        value=data.value,
        status=data.status,
        source=data.source,
        tags=data.tags,
        metadata_=data.metadata,
        first_seen=now,
        last_seen=now,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset(db: Session, asset_id: UUID) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_asset_with_relations(db: Session, asset_id: UUID) -> Optional[AssetWithRelations]:
    asset = get_asset(db, asset_id)
    if not asset:
        return None

    related = []
    for rel in asset.outgoing:
        related.append(RelatedAsset(
            relation_type=rel.relation_type,
            direction="outgoing",
            asset=_to_out(rel.to_asset),
        ))
    for rel in asset.incoming:
        related.append(RelatedAsset(
            relation_type=rel.relation_type,
            direction="incoming",
            asset=_to_out(rel.from_asset),
        ))

    out = AssetWithRelations(**_to_out(asset).model_dump(), related=related)
    return out


def _to_out(asset: Asset) -> AssetOut:
    return AssetOut(
        id=asset.id,
        type=asset.type,
        value=asset.value,
        status=asset.status,
        source=asset.source,
        tags=asset.tags or [],
        metadata=asset.metadata_ or {},
        first_seen=asset.first_seen,
        last_seen=asset.last_seen,
    )


def list_assets(
    db: Session,
    type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    value_contains: Optional[str] = None,
    sort_by: str = "last_seen",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Asset)

    if type:
        query = query.filter(Asset.type == type)
    if status:
        query = query.filter(Asset.status == status)
    if tag:
        # JSON contains check — works on both PostgreSQL and SQLite
        query = query.filter(Asset.tags.cast(String).contains(f'"{tag}"'))
    if value_contains:
        query = query.filter(Asset.value.ilike(f"%{value_contains}%"))

    total = query.count()

    sort_col = getattr(Asset, sort_by, Asset.last_seen)
    if sort_dir == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def update_asset(db: Session, asset_id: UUID, data: AssetUpdate) -> Optional[Asset]:
    asset = get_asset(db, asset_id)
    if not asset:
        return None
    if data.status is not None:
        asset.status = data.status
    if data.tags is not None:
        asset.tags = data.tags
    if data.metadata is not None:
        asset.metadata_ = {**(asset.metadata_ or {}), **data.metadata}
    asset.last_seen = datetime.now(timezone.utc)
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: UUID) -> bool:
    asset = get_asset(db, asset_id)
    if not asset:
        return False
    db.delete(asset)
    db.commit()
    return True


def mark_stale(db: Session, asset_id: UUID) -> Optional[Asset]:
    return update_asset(db, asset_id, AssetUpdate(status=AssetStatus.stale))
