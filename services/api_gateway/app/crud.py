from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException

from robopost_models import Source, Destination, Admin, SourceDestinationMap, AdminDestinationMap
from . import schemas

# --- Source CRUD ---
async def create_source(db: AsyncSession, source: schemas.SourceCreate):
    db_source = Source(name=source.name, url=str(source.url))
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

async def delete_source(db: AsyncSession, source_id: int):
    q = delete(Source).where(Source.id == source_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.commit()

# --- Destination CRUD ---
async def create_destination(db: AsyncSession, destination: schemas.DestinationCreate):
    db_destination = Destination(**destination.dict())
    db.add(db_destination)
    await db.commit()
    await db.refresh(db_destination)
    return db_destination

async def delete_destination(db: AsyncSession, destination_id: int):
    q = delete(Destination).where(Destination.id == destination_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Destination not found")
    await db.commit()

# --- Admin CRUD ---
async def create_admin(db: AsyncSession, admin: schemas.AdminCreate):
    db_admin = Admin(**admin.dict())
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return db_admin

async def delete_admin(db: AsyncSession, admin_id: int):
    q = delete(Admin).where(Admin.id == admin_id)
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    await db.commit()

# --- Mapping CRUD ---
async def link_source_to_destination(db: AsyncSession, source_id: int, destination_id: int):
    # Check if link already exists
    q = select(SourceDestinationMap).where(
        SourceDestinationMap.source_id == source_id,
        SourceDestinationMap.destination_id == destination_id
    )
    existing_link = (await db.execute(q)).scalar_one_or_none()
    if existing_link:
        return existing_link

    db_link = SourceDestinationMap(source_id=source_id, destination_id=destination_id, enabled=True)
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def unlink_source_from_destination(db: AsyncSession, source_id: int, destination_id: int):
    q = delete(SourceDestinationMap).where(
        SourceDestinationMap.source_id == source_id,
        SourceDestinationMap.destination_id == destination_id
    )
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.commit()
    return True

async def assign_admin_to_destination(db: AsyncSession, admin_id: int, destination_id: int):
    q = select(AdminDestinationMap).where(
        AdminDestinationMap.admin_id == admin_id,
        AdminDestinationMap.destination_id == destination_id
    )
    existing_assignment = (await db.execute(q)).scalar_one_or_none()
    if existing_assignment:
        return existing_assignment

    db_assignment = AdminDestinationMap(admin_id=admin_id, destination_id=destination_id)
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

async def unassign_admin_from_destination(db: AsyncSession, admin_id: int, destination_id: int):
    q = delete(AdminDestinationMap).where(
        AdminDestinationMap.admin_id == admin_id,
        AdminDestinationMap.destination_id == destination_id
    )
    result = await db.execute(q)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.commit()
    return True