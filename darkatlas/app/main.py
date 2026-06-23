from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import assets, relationships, import_route
import app.models  # noqa: ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (no-op if already exist)
    try:
        from app.db.base import Base
        from app.db.session import engine
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass  # In tests the DB is managed by the test fixture
    yield


app = FastAPI(
    title="DarkAtlas Asset Management API",
    description="Asset Management module for the DarkAtlas Attack Surface Monitoring platform.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(assets.router, prefix="/api/v1")
app.include_router(relationships.router, prefix="/api/v1")
app.include_router(import_route.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
