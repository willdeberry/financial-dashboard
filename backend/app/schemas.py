from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class SourceEnum(str, Enum):
    bank = "bank"
    credit_card = "credit_card"
    payroll = "payroll"


class TransactionTypeEnum(str, Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"


class StatusEnum(str, Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


class MatchFieldEnum(str, Enum):
    payee = "payee"
    description = "description"


class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryMoveTransactions(BaseModel):
    target_category_id: int


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    transaction_count: int = 0

    model_config = {"from_attributes": True}


class TransactionBase(BaseModel):
    date: datetime
    amount: Decimal
    description: Optional[str] = None
    payee: Optional[str] = None
    source: SourceEnum
    transaction_type: TransactionTypeEnum
    original_text: Optional[str] = None


class TransactionCreate(TransactionBase):
    category_id: Optional[int] = None


class TransactionResponse(TransactionBase):
    id: int
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    excluded: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionCategoryUpdate(BaseModel):
    category_id: int


class TransactionExcludedUpdate(BaseModel):
    excluded: bool


class TransactionTypeUpdate(BaseModel):
    transaction_type: TransactionTypeEnum


class TransactionBulkCategoryUpdate(BaseModel):
    transaction_ids: List[int]
    category_id: int


class TransactionBulkExcludedUpdate(BaseModel):
    transaction_ids: List[int]
    excluded: bool


class TransactionBulkTypeUpdate(BaseModel):
    transaction_ids: List[int]
    transaction_type: TransactionTypeEnum


class UploadHistoryResponse(BaseModel):
    id: int
    filename: str
    source_type: SourceEnum
    upload_date: datetime
    transaction_count: int
    status: StatusEnum
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class CategorizationRuleBase(BaseModel):
    rule_name: str
    match_field: MatchFieldEnum
    match_pattern: str
    category_id: int
    priority: int = 0
    active: bool = True


class CategorizationRuleCreate(CategorizationRuleBase):
    pass


class CategorizationRuleResponse(CategorizationRuleBase):
    id: int

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    category_id: Optional[int]
    category_name: str
    color: Optional[str]
    total: Decimal
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    net: Decimal


class YearlyTrend(BaseModel):
    year: int
    income: Decimal
    expenses: Decimal
    net: Decimal


class TopSpender(BaseModel):
    category_id: Optional[int]
    category_name: str
    color: Optional[str]
    total: Decimal
    count: int


class SummaryStats(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    transaction_count: int


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TransactionResponse]
