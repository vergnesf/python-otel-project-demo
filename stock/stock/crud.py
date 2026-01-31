# pyright: reportMissingImports=false
from sqlalchemy.orm import Session

from common_models.models import WoodType

from . import models, schemas


def get_stocks(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Stock).offset(skip).limit(limit).all()


def create_stock(db: Session, stock: schemas.StockCreate):
    db_stock = (
        db.query(models.Stock).filter(models.Stock.wood_type == stock.wood_type).first()
    )

    if db_stock:
        # Update existing stock
        db_stock.quantity += stock.quantity  # type: ignore[misc]
    else:
        # Create new stock
        db_stock = models.Stock(wood_type=stock.wood_type, quantity=stock.quantity)
        db.add(db_stock)

    db.commit()
    db.refresh(db_stock)
    return db_stock


def get_stock_by_wood_type(db: Session, wood_type: WoodType):
    return db.query(models.Stock).filter(models.Stock.wood_type == wood_type).first()


def decrease_stock_quantity(db: Session, wood_type: str, quantity: int) -> None:
    stock = get_stock_by_wood_type(db, wood_type)
    if stock and stock.quantity is not None and stock.quantity >= quantity:  # type: ignore[misc]
        stock.quantity -= quantity  # type: ignore[misc]
        db.commit()
    else:
        raise ValueError("Insufficient stock or stock not found")
