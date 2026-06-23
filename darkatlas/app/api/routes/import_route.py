from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.session import get_db
from app.schemas.asset import BulkImportRequest, BulkImportResult
from app.services.import_service import bulk_import

router = APIRouter(prefix="/import", tags=["Import"])


@router.post("/", response_model=BulkImportResult, dependencies=[Depends(require_api_key)])
def import_assets(data: BulkImportRequest, db: Session = Depends(get_db)):
    return bulk_import(db, data.assets)
