"""
Bulk import with deduplication.
Dedup key: (type, value) — if an asset with the same type+value exists,
we update last_seen and merge tags/metadata instead of inserting a duplicate.
If a stale asset is re-sighted, it returns to active.
"""
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetStatus
from app.models.relationship import AssetRelationship
from app.schemas.asset import BulkImportItem, BulkImportResult


def bulk_import(db: Session, items: List[BulkImportItem]) -> BulkImportResult:
    created = 0
    updated = 0
    failed = 0
    errors = []

    # First pass: upsert all assets, keep a map of original_id → db UUID
    id_map: dict[str, str] = {}  # dataset id → db UUID (as str)

    for item in items:
        try:
            _validate_item(item)
            asset, was_created = _upsert_asset(db, item)
            if item.id:
                id_map[item.id] = str(asset.id)
            if was_created:
                created += 1
            else:
                updated += 1
        except Exception as e:
            failed += 1
            errors.append(f"Asset '{item.value}': {str(e)}")

    # Second pass: create relationships from parent/covers hints
    for item in items:
        try:
            if item.parent and item.id and item.parent in id_map and item.id in id_map:
                _ensure_relationship(db, id_map[item.id], id_map[item.parent], "subdomain_of")
            if item.covers and item.id and item.covers in id_map and item.id in id_map:
                _ensure_relationship(db, id_map[item.id], id_map[item.covers], "covers")
        except Exception as e:
            errors.append(f"Relationship for '{item.id}': {str(e)}")

    db.commit()
    return BulkImportResult(created=created, updated=updated, failed=failed, errors=errors)


def _validate_item(item: BulkImportItem):
    if not item.value or not item.value.strip():
        raise ValueError("value cannot be empty")
    if not item.type:
        raise ValueError("type is required")


def _upsert_asset(db: Session, item: BulkImportItem):
    now = datetime.now(timezone.utc)
    existing = db.query(Asset).filter(
        Asset.type == item.type,
        Asset.value == item.value,
    ).first()

    if existing:
        # Merge tags (union), merge metadata (incoming wins on conflict)
        existing_tags = set(existing.tags or [])
        existing_tags.update(item.tags)
        existing.tags = list(existing_tags)
        existing.metadata_ = {**(existing.metadata_ or {}), **item.metadata}
        existing.last_seen = now
        # Re-appearing stale asset → active
        if existing.status == AssetStatus.stale:
            existing.status = AssetStatus.active
        return existing, False
    else:
        asset = Asset(
            type=item.type,
            value=item.value,
            status=item.status,
            source=item.source,
            tags=item.tags,
            metadata_=item.metadata,
            first_seen=now,
            last_seen=now,
        )
        db.add(asset)
        db.flush()  # get the ID without committing
        return asset, True


def _ensure_relationship(db: Session, from_id: str, to_id: str, relation_type: str):
    from uuid import UUID
    from_uuid = UUID(from_id)
    to_uuid = UUID(to_id)

    exists = db.query(AssetRelationship).filter(
        AssetRelationship.from_id == from_uuid,
        AssetRelationship.to_id == to_uuid,
        AssetRelationship.relation_type == relation_type,
    ).first()

    if not exists:
        rel = AssetRelationship(from_id=from_uuid, to_id=to_uuid, relation_type=relation_type)
        db.add(rel)
