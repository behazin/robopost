from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException

from . import models, schemas

# --- Source CRUD ---
async def create_source(db: AsyncSession, source: schemas.SourceCreate):
    db_source = models.Source(name=source.name, url=str(source.url))
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

async def delete_source(db: AsyncSession, source_id: int):
    q = delete(models.Source).where(models.Source.id == source_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.commit()

# --- Destination CRUD ---
async def create_destination(db: AsyncSession, destination: schemas.DestinationCreate):
    db_destination = models.Destination(**destination.dict())
    db.add(db_destination)
    await db.commit()
    await db.refresh(db_destination)
    return db_destination

async def delete_destination(db: AsyncSession, destination_id: int):
    q = delete(models.Destination).where(models.Destination.id == destination_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Destination not found")
    await db.commit()

# --- Admin CRUD ---
async def create_admin(db: AsyncSession, admin: schemas.AdminCreate):
    db_admin = models.Admin(**admin.dict())
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return db_admin

async def delete_admin(db: AsyncSession, admin_id: int):
    q = delete(models.Admin).where(models.Admin.id == admin_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    await db.commit()

# --- Mapping CRUD ---
async def link_source_to_destination(db: AsyncSession, source_id: int, destination_id: int):
    # Check if link already exists
    q = select(models.SourceDestinationMap).where(
        models.SourceDestinationMap.source_id == source_id,
        models.SourceDestinationMap.destination_id == destination_id
    )
    existing_link = (await db.execute(q)).scalar_one_or_none()
    if existing_link:
        return existing_link

    db_link = models.SourceDestinationMap(source_id=source_id, destination_id=destination_id, enabled=True)
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def unlink_source_from_destination(db: AsyncSession, source_id: int, destination_id: int):
    q = delete(models.SourceDestinationMap).where(
        models.SourceDestinationMap.source_id == source_id,
        models.SourceDestinationMap.destination_id == destination_id
    )
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.commit()
    return True

async def assign_admin_to_destination(db: AsyncSession, admin_id: int, destination_id: int):
    q = select(models.AdminDestinationMap).where(
        models.AdminDestinationMap.admin_id == admin_id,
        models.AdminDestinationMap.destination_id == destination_id
    )
    existing_assignment = (await db.execute(q)).scalar_one_or_none()
    if existing_assignment:
        return existing_assignment

    db_assignment = models.AdminDestinationMap(admin_id=admin_id, destination_id=destination_id)
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def unassign_admin_from_destination(db: AsyncSession, admin_id: int, destination_id: int):
    q = delete(models.AdminDestinationMap).where(
        models.AdminDestinationMap.admin_id == admin_id,
        models.AdminDestinationMap.destination_id == destination_id
    )
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.commit()
    return True