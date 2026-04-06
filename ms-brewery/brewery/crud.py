"""
This module provides CRUD operations for brews.
"""

from lib_models.models import BrewStatus
from sqlalchemy.orm import Session

from . import models, schemas


def get_brew(db: Session, brew_id: int):
    """
    Retrieve a brew by its ID.
    """
    return db.query(models.BrewModel).filter(models.BrewModel.id == brew_id).first()


def get_brews(db: Session, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of brews with optional pagination.
    """
    return db.query(models.BrewModel).offset(skip).limit(limit).all()


def get_brews_by_status(db: Session, brew_status: BrewStatus, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of brews by status with optional pagination.
    """
    return db.query(models.BrewModel).filter(models.BrewModel.brew_status == brew_status).offset(skip).limit(limit).all()


def update_brew_status(db: Session, brew_id: int, brew_status: BrewStatus):
    """
    Update the status of a brew.
    """
    db_brew = db.query(models.BrewModel).filter(models.BrewModel.id == brew_id).first()
    if db_brew:
        db_brew.brew_status = brew_status  # type: ignore[misc]
        db.commit()
        db.refresh(db_brew)
    return db_brew


def create_brew(db: Session, brew: schemas.BrewCreate):
    """
    Create a new brew.
    """
    db_brew = models.BrewModel(  # pyright: ignore[reportCallIssue]
        ingredient_type=brew.ingredient_type,
        quantity=brew.quantity,
        brew_style=brew.brew_style,
        brew_status=BrewStatus.REGISTERED,
    )
    db.add(db_brew)
    db.commit()
    db.refresh(db_brew)
    return db_brew


def delete_brew(db: Session, brew_id: int):
    """
    Delete a brew by its ID.
    """
    db_brew = db.query(models.BrewModel).filter(models.BrewModel.id == brew_id).first()
    if db_brew:
        db.delete(db_brew)
        db.commit()
    return db_brew
