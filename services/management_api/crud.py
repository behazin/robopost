from sqlalchemy.orm import Session

from . import models, schemas


def create_source(db: Session, source: schemas.SourceCreate) -> models.Source:
    db_source = models.Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


def delete_source(db: Session, source_id: int) -> None:
    db_source = db.get(models.Source, source_id)
    if db_source:
        db.delete(db_source)
        db.commit()


def create_destination(db: Session, destination: schemas.DestinationCreate) -> models.Destination:
    db_destination = models.Destination(**destination.dict())
    db.add(db_destination)
    db.commit()
    db.refresh(db_destination)
    return db_destination


def delete_destination(db: Session, destination_id: int) -> None:
    db_destination = db.get(models.Destination, destination_id)
    if db_destination:
        db.delete(db_destination)
        db.commit()
