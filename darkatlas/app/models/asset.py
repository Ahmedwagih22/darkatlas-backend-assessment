import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Enum
from sqlalchemy.types import TypeDecorator, CHAR
import uuid as _uuid


class UUID(TypeDecorator):
    """Platform-independent UUID type. Uses PostgreSQL's UUID natively,
    falls back to CHAR(36) on other databases (e.g. SQLite for tests)."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PGUUID
            return dialect.type_descriptor(PGUUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return _uuid.UUID(str(value))
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class AssetType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"


class AssetStatus(str, enum.Enum):
    active = "active"
    stale = "stale"
    archived = "archived"


class AssetSource(str, enum.Enum):
    import_ = "import"
    scan = "scan"
    manual = "manual"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(AssetType), nullable=False, index=True)
    value = Column(String, nullable=False, index=True)
    status = Column(Enum(AssetStatus), default=AssetStatus.active, nullable=False, index=True)
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    source = Column(String, nullable=False, default="manual")
    tags = Column(JSON, default=list)  # stored as JSON array; works on both PostgreSQL and SQLite
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    outgoing = relationship("AssetRelationship", foreign_keys="AssetRelationship.from_id", back_populates="from_asset", cascade="all, delete-orphan")
    incoming = relationship("AssetRelationship", foreign_keys="AssetRelationship.to_id", back_populates="to_asset", cascade="all, delete-orphan")
