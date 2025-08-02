import logging
import logging.config
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# The Prometheus instrumentation library is optional during testing.  If it is
# not installed we fall back to a no-op shim so the application can still be
# imported and exercised.
try:  # pragma: no cover - exercised indirectly in tests
    from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class Instrumentator:  # type: ignore
        def instrument(self, app):
            return self

        def expose(self, app, include_in_schema=False):
            return self


from . import crud, schemas
from .db import get_db, init_db

LOGGING_CONFIG = Path(__file__).resolve().parent.parent / "logging.conf"
if not LOGGING_CONFIG.exists():
    LOGGING_CONFIG = Path(__file__).resolve().parents[3] / "logging.conf"
if LOGGING_CONFIG.exists():
    logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)
else:  # pragma: no cover - default logging setup for tests
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RoboPost API Gateway",
    description="Manages sources, destinations, admins, and their relationships.",
    version="1.0.0"
)

# Prometheus Metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)

@app.on_event("startup")
async def startup():
    logger.info("Initializing database...")
    await init_db()
    logger.info("API Gateway started.")

@app.get("/healthz", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

# --- Sources Endpoints ---
@app.post("/sources", response_model=schemas.Source, status_code=201, tags=["Sources"])
async def create_source(source: schemas.SourceCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_source(db=db, source=source)

@app.delete("/sources/{source_id}", status_code=204, tags=["Sources"])
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_source(db=db, source_id=source_id)
    return {"ok": True}

# --- Destinations Endpoints ---
@app.post("/destinations", response_model=schemas.Destination, status_code=201, tags=["Destinations"])
async def create_destination(destination: schemas.DestinationCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_destination(db=db, destination=destination)

@app.delete("/destinations/{destination_id}", status_code=204, tags=["Destinations"])
async def delete_destination(destination_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_destination(db=db, destination_id=destination_id)
    return {"ok": True}

# --- Admins Endpoints ---
@app.post("/admins", response_model=schemas.Admin, status_code=201, tags=["Admins"])
async def create_admin(admin: schemas.AdminCreate, db: AsyncSession = Depends(get_db)):
    # You might want to add a check for uniqueness on telegram_id here
    return await crud.create_admin(db=db, admin=admin)

@app.delete("/admins/{admin_id}", status_code=204, tags=["Admins"])
async def delete_admin(admin_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_admin(db=db, admin_id=admin_id)
    return {"ok": True}

# --- Mapping Endpoints ---
@app.post("/sources/{source_id}/link/{destination_id}", response_model=schemas.SourceDestinationMap, tags=["Mapping"])
async def link_source_to_destination(source_id: int, destination_id: int, db: AsyncSession = Depends(get_db)):
    """Links a source to a destination."""
    link = await crud.link_source_to_destination(db, source_id=source_id, destination_id=destination_id)
    if not link:
        raise HTTPException(status_code=404, detail="Source or Destination not found")
    return link

@app.delete("/sources/{source_id}/unlink/{destination_id}", status_code=204, tags=["Mapping"])
async def unlink_source_from_destination(source_id: int, destination_id: int, db: AsyncSession = Depends(get_db)):
    """Unlinks a source from a destination."""
    await crud.unlink_source_from_destination(db, source_id=source_id, destination_id=destination_id)
    return {"ok": True}

@app.post("/admins/{admin_id}/assign/{destination_id}", response_model=schemas.AdminDestinationMap, tags=["Mapping"])
async def assign_admin_to_destination(admin_id: int, destination_id: int, db: AsyncSession = Depends(get_db)):
    """Assigns an admin to manage a destination."""
    assignment = await crud.assign_admin_to_destination(db, admin_id=admin_id, destination_id=destination_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Admin or Destination not found")
    return assignment

@app.delete("/admins/{admin_id}/unassign/{destination_id}", status_code=204, tags=["Mapping"])
async def unassign_admin_from_destination(admin_id: int, destination_id: int, db: AsyncSession = Depends(get_db)):
    """Unassigns an admin from a destination."""
    await crud.unassign_admin_from_destination(db, admin_id=admin_id, destination_id=destination_id)
    return {"ok": True}