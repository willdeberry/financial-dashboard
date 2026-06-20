from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/categories", response_model=List[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()


@router.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    if db.query(models.Category).filter(models.Category.name == category.name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    db_cat = models.Category(**category.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


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
