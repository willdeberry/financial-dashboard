from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/transactions", response_model=schemas.PaginatedTransactions)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_ids: Optional[List[int]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    transaction_types: Optional[List[str]] = Query(None),
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort_by: str = Query("date", pattern="^(date|amount|payee|category)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction).join(models.Category, isouter=True)

    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    if category_ids:
        real_ids = [i for i in category_ids if i != 0]
        include_null = 0 in category_ids
        if real_ids and include_null:
            query = query.filter(
                or_(models.Transaction.category_id.in_(real_ids), models.Transaction.category_id.is_(None))
            )
        elif real_ids:
            query = query.filter(models.Transaction.category_id.in_(real_ids))
        elif include_null:
            query = query.filter(models.Transaction.category_id.is_(None))
    if sources:
        query = query.filter(models.Transaction.source.in_(sources))
    if transaction_types:
        query = query.filter(models.Transaction.transaction_type.in_(transaction_types))
    if min_amount is not None:
        query = query.filter(models.Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(models.Transaction.amount <= max_amount)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(models.Transaction.payee.ilike(term), models.Transaction.description.ilike(term))
        )

    total = query.count()

    sort_col = {
        "date": models.Transaction.date,
        "amount": models.Transaction.amount,
        "payee": models.Transaction.payee,
        "category": models.Category.name,
    }.get(sort_by, models.Transaction.date)

    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.put("/transactions/bulk-category")
def bulk_update_category(
    update: schemas.TransactionBulkCategoryUpdate,
    db: Session = Depends(get_db),
):
    if not update.transaction_ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")
    if not db.query(models.Category).filter(models.Category.id == update.category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")
    updated = (
        db.query(models.Transaction)
        .filter(models.Transaction.id.in_(update.transaction_ids))
        .update({"category_id": update.category_id}, synchronize_session=False)
    )
    db.commit()
    return {"updated": updated}


@router.put("/transactions/bulk-excluded")
def bulk_update_excluded(
    update: schemas.TransactionBulkExcludedUpdate,
    db: Session = Depends(get_db),
):
    if not update.transaction_ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")
    updated = (
        db.query(models.Transaction)
        .filter(models.Transaction.id.in_(update.transaction_ids))
        .update({"excluded": update.excluded}, synchronize_session=False)
    )
    db.commit()
    return {"updated": updated}


@router.put("/transactions/bulk-type")
def bulk_update_type(
    update: schemas.TransactionBulkTypeUpdate,
    db: Session = Depends(get_db),
):
    if not update.transaction_ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")
    updated = (
        db.query(models.Transaction)
        .filter(models.Transaction.id.in_(update.transaction_ids))
        .update({"transaction_type": update.transaction_type}, synchronize_session=False)
    )
    db.commit()
    return {"updated": updated}


@router.put("/transactions/{transaction_id}/type", response_model=schemas.TransactionResponse)
def update_transaction_type(
    transaction_id: int,
    update: schemas.TransactionTypeUpdate,
    db: Session = Depends(get_db),
):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    transaction.transaction_type = update.transaction_type
    db.commit()
    db.refresh(transaction)
    return transaction


@router.put("/transactions/{transaction_id}/category", response_model=schemas.TransactionResponse)
def update_transaction_category(
    transaction_id: int,
    update: schemas.TransactionCategoryUpdate,
    db: Session = Depends(get_db),
):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not db.query(models.Category).filter(models.Category.id == update.category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")

    transaction.category_id = update.category_id
    db.commit()
    db.refresh(transaction)
    return transaction


@router.put("/transactions/{transaction_id}/excluded", response_model=schemas.TransactionResponse)
def update_transaction_excluded(
    transaction_id: int,
    update: schemas.TransactionExcludedUpdate,
    db: Session = Depends(get_db),
):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    transaction.excluded = update.excluded
    db.commit()
    db.refresh(transaction)
    return transaction
