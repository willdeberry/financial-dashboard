import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, Enum,
    Text, Boolean, ForeignKey, Index,
)
from sqlalchemy.orm import relationship
from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7))
    icon = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="category")
    rules = relationship("CategorizationRule", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description = Column(String(500))
    payee = Column(String(255))
    source = Column(Enum("bank", "credit_card", "payroll"), nullable=False)
    transaction_type = Column(Enum("income", "expense", "transfer"), nullable=False)
    original_text = Column(Text)
    excluded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    category = relationship("Category", back_populates="transactions")

    __table_args__ = (
        Index("idx_date_category_source", "date", "category_id", "source"),
    )


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    source_type = Column(Enum("bank", "credit_card", "payroll"), nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_count = Column(Integer, default=0)
    status = Column(Enum("pending", "processed", "failed"), default="pending")
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)


class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(255), nullable=False)
    match_field = Column(Enum("payee", "description"), nullable=False)
    match_pattern = Column(String(500), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="rules")
