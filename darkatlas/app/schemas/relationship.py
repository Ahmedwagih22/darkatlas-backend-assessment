from uuid import UUID
from pydantic import BaseModel
from app.schemas.asset import AssetOut


class RelationshipCreate(BaseModel):
    from_id: UUID
    to_id: UUID
    relation_type: str


class RelationshipOut(BaseModel):
    id: UUID
    from_id: UUID
    to_id: UUID
    relation_type: str
    from_asset: AssetOut
    to_asset: AssetOut

    model_config = {"from_attributes": True}
