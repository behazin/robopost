from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.post("/", response_model=schemas.Destination)
def create_destination(destination: schemas.DestinationCreate, db: Session = Depends(get_db)):
    return crud.create_destination(db, destination)


@router.delete("/{destination_id}")
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    crud.delete_destination(db, destination_id)
    return {"status": "deleted"}
