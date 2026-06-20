from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
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
    category_ids: Optional[str] = None,
    sources: Optional[str] = None,
    transaction_types: Optional[str] = None,
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
        ids = [int(x) for x in category_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(models.Transaction.category_id.in_(ids))
    if sources:
        query = query.filter(models.Transaction.source.in_([s.strip() for s in sources.split(",")]))
    if transaction_types:
        query = query.filter(models.Transaction.transaction_type.in_([t.strip() for t in transaction_types.split(",")]))
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
