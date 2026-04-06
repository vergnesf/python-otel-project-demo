# pyright: reportMissingImports=false
from lib_models.models import IngredientNotFoundError, IngredientType, InsufficientIngredientError
from sqlalchemy.orm import Session

from . import models, schemas


def get_ingredients(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.IngredientStockModel).offset(skip).limit(limit).all()


def create_ingredient(db: Session, ingredient: schemas.IngredientCreate):
    db_ingredient = db.query(models.IngredientStockModel).filter(models.IngredientStockModel.ingredient_type == ingredient.ingredient_type).first()

    if db_ingredient:
        # Accumulate existing stock
        db_ingredient.quantity += ingredient.quantity  # type: ignore[misc]
    else:
        # Create new ingredient stock entry
        db_ingredient = models.IngredientStockModel(ingredient_type=ingredient.ingredient_type, quantity=ingredient.quantity)  # pyright: ignore[reportCallIssue]
        db.add(db_ingredient)

    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def get_ingredient_by_type(db: Session, ingredient_type: IngredientType):
    return db.query(models.IngredientStockModel).filter(models.IngredientStockModel.ingredient_type == ingredient_type).first()


def decrease_ingredient_quantity(db: Session, ingredient_type: str, quantity: int) -> None:
    ingredient = get_ingredient_by_type(db, ingredient_type)  # type: ignore[arg-type]
    if ingredient is None:
        raise IngredientNotFoundError(ingredient_type)
    if ingredient.quantity is None or ingredient.quantity < quantity:  # type: ignore[misc]
        raise InsufficientIngredientError(ingredient_type, requested=quantity, available=ingredient.quantity or 0)  # pyright: ignore[reportArgumentType]
    ingredient.quantity -= quantity  # type: ignore[misc]
    db.commit()
