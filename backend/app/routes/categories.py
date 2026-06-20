from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter()


def _categories_with_counts(db: Session):
    counts = (
        db.query(models.Transaction.category_id, func.count().label("cnt"))
        .group_by(models.Transaction.category_id)
        .subquery()
    )
    rows = (
        db.query(models.Category, func.coalesce(counts.c.cnt, 0).label("transaction_count"))
        .outerjoin(counts, models.Category.id == counts.c.category_id)
        .order_by(models.Category.name)
        .all()
    )
    result = []
    for cat, count in rows:
        cat.transaction_count = count
        result.append(cat)
    return result


@router.get("/categories", response_model=List[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return _categories_with_counts(db)


@router.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    if db.query(models.Category).filter(models.Category.name == category.name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    db_cat = models.Category(**category.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    db_cat.transaction_count = 0
    return db_cat


@router.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    update: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    if update.name is not None and update.name != cat.name:
        if db.query(models.Category).filter(models.Category.name == update.name).first():
            raise HTTPException(status_code=400, detail="Category name already exists")
        cat.name = update.name
    if update.color is not None:
        cat.color = update.color
    if update.icon is not None:
        cat.icon = update.icon

    db.commit()
    db.refresh(cat)
    cat.transaction_count = (
        db.query(func.count(models.Transaction.id))
        .filter(models.Transaction.category_id == category_id)
        .scalar()
    )
    return cat


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    reassign_to: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    tx_count = (
        db.query(func.count(models.Transaction.id))
        .filter(models.Transaction.category_id == category_id)
        .scalar()
    )

    if tx_count > 0:
        if reassign_to is None:
            raise HTTPException(
                status_code=400,
                detail=f"Category has {tx_count} transactions. Provide reassign_to to move them first.",
            )
        target = db.query(models.Category).filter(models.Category.id == reassign_to).first()
        if not target:
            raise HTTPException(status_code=404, detail="Reassign target category not found")
        db.query(models.Transaction).filter(
            models.Transaction.category_id == category_id
        ).update({"category_id": reassign_to})

    db.delete(cat)
    db.commit()


@router.post("/categories/{category_id}/move-transactions", response_model=schemas.CategoryResponse)
def move_transactions(
    category_id: int,
    body: schemas.CategoryMoveTransactions,
    db: Session = Depends(get_db),
):
    source = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source category not found")
    target = db.query(models.Category).filter(models.Category.id == body.target_category_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target category not found")
    if category_id == body.target_category_id:
        raise HTTPException(status_code=400, detail="Source and target must differ")

    db.query(models.Transaction).filter(
        models.Transaction.category_id == category_id
    ).update({"category_id": body.target_category_id})
    db.commit()
    db.refresh(source)
    source.transaction_count = 0
    return source


@router.get("/categories/rules", response_model=List[schemas.CategorizationRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return (
        db.query(models.CategorizationRule)
        .order_by(models.CategorizationRule.priority.desc())
        .all()
    )


@router.post("/categories/rules", response_model=schemas.CategorizationRuleResponse, status_code=201)
def create_rule(rule: schemas.CategorizationRuleCreate, db: Session = Depends(get_db)):
    db_rule = models.CategorizationRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule
