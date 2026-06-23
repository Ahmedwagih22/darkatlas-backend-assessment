from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.session import get_db
from app.models.relationship import AssetRelationship
from app.models.asset import Asset
from app.schemas.relationship import RelationshipCreate, RelationshipOut
from app.services.asset_service import _to_out

router = APIRouter(prefix="/relationships", tags=["Relationships"])


@router.post("/", response_model=RelationshipOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_relationship(data: RelationshipCreate, db: Session = Depends(get_db)):
    from_asset = db.query(Asset).filter(Asset.id == data.from_id).first()
    to_asset = db.query(Asset).filter(Asset.id == data.to_id).first()
    if not from_asset or not to_asset:
        raise HTTPException(status_code=404, detail="One or both assets not found")

    # Prevent duplicates
    existing = db.query(AssetRelationship).filter(
        AssetRelationship.from_id == data.from_id,
        AssetRelationship.to_id == data.to_id,
        AssetRelationship.relation_type == data.relation_type,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Relationship already exists")

    rel = AssetRelationship(from_id=data.from_id, to_id=data.to_id, relation_type=data.relation_type)
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return RelationshipOut(
        id=rel.id,
        from_id=rel.from_id,
        to_id=rel.to_id,
        relation_type=rel.relation_type,
        from_asset=_to_out(rel.from_asset),
        to_asset=_to_out(rel.to_asset),
    )


@router.get("/", response_model=list[RelationshipOut])
def list_relationships(db: Session = Depends(get_db)):
    rels = db.query(AssetRelationship).all()
    return [
        RelationshipOut(
            id=r.id, from_id=r.from_id, to_id=r.to_id, relation_type=r.relation_type,
            from_asset=_to_out(r.from_asset), to_asset=_to_out(r.to_asset),
        ) for r in rels
    ]


@router.delete("/{rel_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_relationship(rel_id: UUID, db: Session = Depends(get_db)):
    rel = db.query(AssetRelationship).filter(AssetRelationship.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(rel)
    db.commit()
