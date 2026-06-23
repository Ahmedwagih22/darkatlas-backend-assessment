import uuid
from sqlalchemy import Column, String, ForeignKey
from app.models.asset import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    from_id = Column(UUID(), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    to_id = Column(UUID(), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String, nullable=False)  # e.g. "subdomain_of", "resolves_to", "covers"

    from_asset = relationship("Asset", foreign_keys=[from_id], back_populates="outgoing")
    to_asset = relationship("Asset", foreign_keys=[to_id], back_populates="incoming")
