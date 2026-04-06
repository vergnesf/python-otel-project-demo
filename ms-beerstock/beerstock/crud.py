# pyright: reportMissingImports=false
from lib_models.models import BrewStyle, InsufficientBeerStockError
from sqlalchemy.orm import Session

from . import models, schemas


def get_beer_stocks(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.BeerStockModel).offset(skip).limit(limit).all()


def create_beer_stock(db: Session, stock: schemas.BeerStockCreate):
    db_stock = db.query(models.BeerStockModel).filter(models.BeerStockModel.brew_style == stock.brew_style).first()

    if db_stock:
        # Accumulate existing stock
        db_stock.quantity += stock.quantity  # type: ignore[misc]
    else:
        # Create new beer stock entry
        db_stock = models.BeerStockModel(brew_style=stock.brew_style, quantity=stock.quantity)  # pyright: ignore[reportCallIssue]
        db.add(db_stock)

    db.commit()
    db.refresh(db_stock)
    return db_stock


def get_beer_stock_by_style(db: Session, brew_style: BrewStyle):
    return db.query(models.BeerStockModel).filter(models.BeerStockModel.brew_style == brew_style).first()


def ship_beer_stock(db: Session, brew_style: str, quantity: int) -> None:
    stock = get_beer_stock_by_style(db, brew_style)  # type: ignore[arg-type]
    if stock is None or stock.quantity is None or stock.quantity < quantity:  # type: ignore[misc]
        available = stock.quantity if stock is not None else 0
        raise InsufficientBeerStockError(brew_style, requested=quantity, available=available or 0)  # pyright: ignore[reportArgumentType]
    stock.quantity -= quantity  # type: ignore[misc]
    db.commit()
