from __future__ import annotations
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, field_validator
from app.models.asset import AssetType, AssetStatus


class AssetBase(BaseModel):
    type: AssetType
    value: str
    status: AssetStatus = AssetStatus.active
    source: str = "manual"
    tags: List[str] = []
    metadata: dict[str, Any] = {}


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    status: Optional[AssetStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict[str, Any]] = None
    last_seen: Optional[datetime] = None


class AssetOut(AssetBase):
    id: UUID
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        # Map metadata_ ORM field → metadata in schema
        if hasattr(obj, "metadata_"):
            obj.__dict__.setdefault("metadata", obj.metadata_)
        return super().model_validate(obj, *args, **kwargs)


class AssetWithRelations(AssetOut):
    related: List["RelatedAsset"] = []


class RelatedAsset(BaseModel):
    relation_type: str
    direction: str  # "outgoing" or "incoming"
    asset: AssetOut

    model_config = {"from_attributes": True}


# Bulk import
class BulkImportItem(BaseModel):
    id: Optional[str] = None
    type: AssetType
    value: str
    status: AssetStatus = AssetStatus.active
    source: str = "import"
    tags: List[str] = []
    metadata: dict[str, Any] = {}
    # Optional relationship hints from dataset
    parent: Optional[str] = None
    covers: Optional[str] = None


class BulkImportRequest(BaseModel):
    assets: List[BulkImportItem]


class BulkImportResult(BaseModel):
    created: int
    updated: int
    failed: int
    errors: List[str] = []


# Pagination
class PaginatedAssets(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AssetOut]
