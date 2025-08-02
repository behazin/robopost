from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=schemas.Source)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    return crud.create_source(db, source)


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    crud.delete_source(db, source_id)
    return {"status": "deleted"}
