from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from . import crud, schemas, db

router = APIRouter(prefix="/api/v1", tags=["Management API"])

# --- Dependency ---
async def get_db_session() -> AsyncSession:
    """
    Provides a database session for a single request.
    """
    async with db.SessionLocal() as session:
        yield session

# =================================================================
# 🐍 Sources Endpoints
# =================================================================

@router.post("/sources", response_model=schemas.Source, status_code=status.HTTP_201_CREATED, summary="Create a new source")
async def create_source(source: schemas.SourceCreate, db_session: AsyncSession = Depends(get_db_session)):
    """
    Creates a new content source (e.g., an RSS feed).
    - **name**: A user-friendly name for the source.
    - **url**: The unique URL of the feed.
    """
    db_source = await crud.get_source_by_url(db_session, url=source.url)
    if db_source:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source URL already registered")
    return await crud.create_source(db_session=db_session, source=source)

@router.get("/sources", response_model=List[schemas.Source], summary="Get all sources")
async def read_sources(skip: int = 0, limit: int = 100, db_session: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a list of all configured sources.
    """
    sources = await crud.get_sources(db_session, skip=skip, limit=limit)
    return sources

@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a source")
async def delete_source(source_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Deletes a source by its ID. This will also remove any associated links
    to destinations.
    """
    if not await crud.delete_source(db_session, source_id=source_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return

# =================================================================
# 🎯 Destinations Endpoints
# =================================================================

@router.post("/destinations", response_model=schemas.Destination, status_code=status.HTTP_201_CREATED, summary="Create a new destination")
async def create_destination(destination: schemas.DestinationCreate, db_session: AsyncSession = Depends(get_db_session)):
    """
    Creates a new publication destination (e.g., a Telegram channel or a WordPress site).
    - **name**: A user-friendly name for the destination.
    - **platform**: The platform type (TELEGRAM, WORDPRESS, etc.).
    - **credentials**: A JSON object with authentication details.
    - **rate_limit_per_minute**: Optional limit on posts per minute.
    """
    return await crud.create_destination(db_session=db_session, destination=destination)

@router.get("/destinations", response_model=List[schemas.Destination], summary="Get all destinations")
async def read_destinations(skip: int = 0, limit: int = 100, db_session: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a list of all configured destinations.
    """
    destinations = await crud.get_destinations(db_session, skip=skip, limit=limit)
    return destinations

@router.delete("/destinations/{destination_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a destination")
async def delete_destination(destination_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Deletes a destination by its ID.
    """
    if not await crud.delete_destination(db_session, destination_id=destination_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")
    return

# =================================================================
# 🔗 Linking Endpoints (Source <-> Destination)
# =================================================================

@router.post("/sources/{source_id}/link/{destination_id}", response_model=schemas.SourceDestinationMap, status_code=status.HTTP_201_CREATED, summary="Link a source to a destination")
async def link_source_to_destination(source_id: int, destination_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Creates an active link between a source and a destination. Content from the
    source will now be eligible for publication to this destination.
    """
    link = await crud.link_source_to_destination(db_session, source_id, destination_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or Destination not found")
    return link

@router.delete("/sources/{source_id}/unlink/{destination_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unlink a source from a destination")
async def unlink_source_from_destination(source_id: int, destination_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Removes the link between a source and a destination.
    """
    if not await crud.unlink_source_from_destination(db_session, source_id, destination_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return

# =================================================================
# 🧑‍💻 Admins Endpoints
# =================================================================

@router.post("/admins", response_model=schemas.Admin, status_code=status.HTTP_201_CREATED, summary="Create a new admin")
async def create_admin(admin: schemas.AdminCreate, db_session: AsyncSession = Depends(get_db_session)):
    """
    Registers a new admin in the system.
    - **telegram_id**: The unique Telegram user ID.
    - **name**: The admin's name.
    """
    db_admin = await crud.get_admin_by_telegram_id(db_session, telegram_id=admin.telegram_id)
    if db_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin with this Telegram ID already exists")
    return await crud.create_admin(db_session, admin)

@router.get("/admins", response_model=List[schemas.Admin], summary="Get all admins")
async def read_admins(skip: int = 0, limit: int = 100, db_session: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a list of all registered admins.
    """
    admins = await crud.get_admins(db_session, skip=skip, limit=limit)
    return admins

@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an admin")
async def delete_admin(admin_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Deletes an admin by their internal ID.
    """
    if not await crud.delete_admin(db_session, admin_id=admin_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return

# =================================================================
# 🧑‍💻🔗 Linking Endpoints (Admin <-> Destination)
# =================================================================

@router.post("/admins/{admin_id}/link_destination/{destination_id}", status_code=status.HTTP_201_CREATED, summary="Assign a destination to an admin")
async def link_admin_to_destination(admin_id: int, destination_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Gives an admin permission to manage a specific destination (i.e., approve/reject content).
    """
    link = await crud.link_admin_to_destination(db_session, admin_id=admin_id, destination_id=destination_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin or Destination not found")
    return {"message": "Admin successfully linked to destination."}

@router.delete("/admins/{admin_id}/unlink_destination/{destination_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unassign a destination from an admin")
async def unlink_admin_from_destination(admin_id: int, destination_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """
    Revokes an admin's permission to manage a specific destination.
    """
    if not await crud.unlink_admin_from_destination(db_session, admin_id=admin_id, destination_id=destination_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin-Destination link not found")
    return