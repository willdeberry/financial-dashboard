"""
End-to-end filter validation using SQLite + httpx.
Tests: category filter with date range, date range on analytics endpoints.
"""
from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── patch DB before importing app ──────────────────────────────────────────
import os
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")

from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import models
from app.main import app

# StaticPool keeps a single connection so create_all and test queries
# see the same in-memory database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# ── seed data ───────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db = TestingSession()

cat_grocery = models.Category(name="Groceries", color="#22c55e")
cat_dining  = models.Category(name="Dining",    color="#f97316")
db.add_all([cat_grocery, cat_dining])
db.commit()

GROCERY_ID = cat_grocery.id
DINING_ID  = cat_dining.id

txns = [
    # Jan — Groceries
    models.Transaction(date=datetime(2026, 1, 5),  amount=Decimal("80"),  description="Walmart",  payee="Walmart",  source="bank", transaction_type="expense", category_id=GROCERY_ID),
    # Feb — Dining
    models.Transaction(date=datetime(2026, 2, 10), amount=Decimal("45"),  description="Chipotle", payee="Chipotle", source="bank", transaction_type="expense", category_id=DINING_ID),
    # Mar — Groceries
    models.Transaction(date=datetime(2026, 3, 15), amount=Decimal("120"), description="Kroger",   payee="Kroger",   source="bank", transaction_type="expense", category_id=GROCERY_ID),
    # Apr — Uncategorized
    models.Transaction(date=datetime(2026, 4, 20), amount=Decimal("200"), description="Mystery",  payee="Mystery",  source="bank", transaction_type="expense", category_id=None),
    # May — income uncategorized
    models.Transaction(date=datetime(2026, 5, 1),  amount=Decimal("5000"),description="Payroll",  payee="Payroll",  source="bank", transaction_type="income",  category_id=None),
]
db.add_all(txns)
db.commit()
db.close()

# ── tests ───────────────────────────────────────────────────────────────────
client = TestClient(app)


def get_txns(**params):
    r = client.get("/transactions", params=params)
    assert r.status_code == 200, r.text
    return r.json()["items"]


def test_category_filter_alone():
    items = get_txns(category_ids=GROCERY_ID)
    assert len(items) == 2
    assert all(t["category"]["name"] == "Groceries" for t in items)


def test_date_range_alone():
    items = get_txns(start_date="2026-02-01", end_date="2026-03-31")
    assert len(items) == 2  # Feb + Mar


def test_category_filter_with_date_range():
    """BUG 1: category filter must still work when a date range is set."""
    items = get_txns(
        start_date="2026-01-01",
        end_date="2026-06-30",
        category_ids=GROCERY_ID,
    )
    assert len(items) == 2, f"Expected 2 Grocery txns, got {len(items)}: {[(t['payee'], t['date']) for t in items]}"
    assert all(t["category"]["name"] == "Groceries" for t in items)


def test_multiple_categories_with_date_range():
    items = get_txns(
        start_date="2026-01-01",
        end_date="2026-06-30",
        category_ids=[GROCERY_ID, DINING_ID],
    )
    assert len(items) == 3, f"Expected 3 (2 grocery + 1 dining), got {len(items)}"


def test_uncategorized_filter():
    items = get_txns(category_ids=0)
    assert len(items) == 2  # Mystery + Payroll (both have category_id=None)


def test_uncategorized_with_date_range():
    items = get_txns(start_date="2026-04-01", end_date="2026-04-30", category_ids=0)
    assert len(items) == 1
    assert items[0]["payee"] == "Mystery"


def test_uncategorized_combined_with_category():
    # 0 + GROCERY_ID → uncategorized OR groceries
    items = get_txns(category_ids=[0, GROCERY_ID])
    assert len(items) == 4  # 2 grocery + 2 uncategorized


def test_date_range_no_results():
    items = get_txns(start_date="2025-01-01", end_date="2025-12-31")
    assert len(items) == 0


def test_analytics_by_category_date_range():
    """BUG 2 (partial): by-category respects date range."""
    r = client.get("/analytics/by-category", params={"transaction_type": "expense", "start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert r.status_code == 200, r.text
    data = r.json()
    # Only January has Groceries ($80), nothing else in range
    names = [d["category_name"] for d in data]
    assert "Groceries" in names
    assert "Dining" not in names, f"Dining should not appear in Jan-only range, got: {names}"


def test_analytics_by_category_no_date_range():
    """Without date filter all categories appear."""
    r = client.get("/analytics/by-category", params={"transaction_type": "expense"})
    assert r.status_code == 200, r.text
    names = [d["category_name"] for d in r.json()]
    assert "Groceries" in names
    assert "Dining" in names


def test_analytics_summary_date_range():
    """Summary numbers change when date range is applied."""
    r_all  = client.get("/analytics/summary")
    r_jan  = client.get("/analytics/summary", params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert r_all.status_code == r_jan.status_code == 200
    total_expenses = float(r_all.json()["total_expenses"])
    jan_expenses   = float(r_jan.json()["total_expenses"])
    assert jan_expenses < total_expenses, "Jan-only expenses should be less than all-time"
    assert jan_expenses == 80.0, f"Jan should be $80 (Walmart), got {jan_expenses}"


if __name__ == "__main__":
    tests = [
        test_category_filter_alone,
        test_date_range_alone,
        test_category_filter_with_date_range,
        test_multiple_categories_with_date_range,
        test_uncategorized_filter,
        test_uncategorized_with_date_range,
        test_uncategorized_combined_with_category,
        test_date_range_no_results,
        test_analytics_by_category_date_range,
        test_analytics_by_category_no_date_range,
        test_analytics_summary_date_range,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
