from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from .. import models, schemas
from ..database import get_db

router = APIRouter()

_zero = Decimal("0")


def _income_expr():
    return func.sum(
        case((models.Transaction.transaction_type == "income", models.Transaction.amount), else_=0)
    )


def _expense_expr():
    return func.sum(
        case((models.Transaction.transaction_type == "expense", models.Transaction.amount), else_=0)
    )


@router.get("/analytics/summary", response_model=schemas.SummaryStats)
def analytics_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    query = db.query(_income_expr().label("income"), _expense_expr().label("expenses"), func.count(models.Transaction.id).label("count"))
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    r = query.one()
    income = r.income or _zero
    expenses = r.expenses or _zero
    return {"total_income": income, "total_expenses": expenses, "net": income - expenses, "transaction_count": r.count or 0}


@router.get("/analytics/by-category", response_model=List[schemas.CategoryBreakdown])
def analytics_by_category(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(
        models.Transaction.category_id,
        func.coalesce(models.Category.name, "Uncategorized").label("category_name"),
        func.coalesce(models.Category.color, "#9ca3af").label("color"),
        func.sum(models.Transaction.amount).label("total"),
        func.count(models.Transaction.id).label("count"),
    ).join(models.Category, models.Transaction.category_id == models.Category.id, isouter=True)

    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    if transaction_type:
        query = query.filter(models.Transaction.transaction_type == transaction_type)

    results = query.group_by(
        models.Transaction.category_id, models.Category.name, models.Category.color
    ).order_by(func.sum(models.Transaction.amount).desc()).all()

    return [
        {"category_id": r.category_id, "category_name": r.category_name, "color": r.color, "total": r.total or _zero, "count": r.count}
        for r in results
    ]


@router.get("/analytics/monthly-trend", response_model=List[schemas.MonthlyTrend])
def analytics_monthly_trend(year: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(
        func.year(models.Transaction.date).label("year"),
        func.month(models.Transaction.date).label("month"),
        _income_expr().label("income"),
        _expense_expr().label("expenses"),
    )
    if year:
        query = query.filter(func.year(models.Transaction.date) == year)

    results = query.group_by(
        func.year(models.Transaction.date), func.month(models.Transaction.date)
    ).order_by(func.year(models.Transaction.date), func.month(models.Transaction.date)).all()

    return [
        {"year": r.year, "month": r.month, "income": r.income or _zero, "expenses": r.expenses or _zero, "net": (r.income or _zero) - (r.expenses or _zero)}
        for r in results
    ]


@router.get("/analytics/yearly-trend", response_model=List[schemas.YearlyTrend])
def analytics_yearly_trend(db: Session = Depends(get_db)):
    results = db.query(
        func.year(models.Transaction.date).label("year"),
        _income_expr().label("income"),
        _expense_expr().label("expenses"),
    ).group_by(func.year(models.Transaction.date)).order_by(func.year(models.Transaction.date)).all()

    return [
        {"year": r.year, "income": r.income or _zero, "expenses": r.expenses or _zero, "net": (r.income or _zero) - (r.expenses or _zero)}
        for r in results
    ]


@router.get("/analytics/top-spenders", response_model=List[schemas.TopSpender])
def analytics_top_spenders(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(
        models.Transaction.category_id,
        func.coalesce(models.Category.name, "Uncategorized").label("category_name"),
        func.coalesce(models.Category.color, "#9ca3af").label("color"),
        func.sum(models.Transaction.amount).label("total"),
        func.count(models.Transaction.id).label("count"),
    ).join(models.Category, models.Transaction.category_id == models.Category.id, isouter=True).filter(
        models.Transaction.transaction_type == "expense"
    )

    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)

    results = query.group_by(
        models.Transaction.category_id, models.Category.name, models.Category.color
    ).order_by(func.sum(models.Transaction.amount).desc()).limit(limit).all()

    return [
        {"category_id": r.category_id, "category_name": r.category_name, "color": r.color, "total": r.total or _zero, "count": r.count}
        for r in results
    ]
