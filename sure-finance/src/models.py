"""Data models for Sure Finance API.

This module contains Pydantic models representing the data structures
used by the Sure Finance API.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    INCOME = "income"
    EXPENSE = "expense"
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class AccountClassification(str, Enum):
    """Account classification enumeration."""
    ASSET = "asset"
    LIABILITY = "liability"
    INCOME = "income"
    EXPENSE = "expense"


class CategoryClassification(str, Enum):
    """Category classification enumeration."""
    INCOME = "income"
    EXPENSE = "expense"


class ImportStatus(str, Enum):
    """Import status enumeration."""
    PENDING = "pending"
    COMPLETE = "complete"
    IMPORTING = "importing"
    REVERTING = "reverting"
    REVERT_FAILED = "revert_failed"
    FAILED = "failed"


class TradeType(str, Enum):
    """Trade type enumeration."""
    BUY = "buy"
    SELL = "sell"


class BaseEntity(BaseModel):
    """Base model for API entities."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Account(BaseEntity):
    """Account model."""
    name: str
    account_type: str
    balance: Optional[Decimal] = None
    currency: Optional[str] = None
    classification: Optional[AccountClassification] = None


class Category(BaseEntity):
    """Category model."""
    name: str
    classification: CategoryClassification
    color: str
    icon: str
    parent_id: Optional[UUID] = None
    parent: Optional['Category'] = None
    subcategories_count: int = 0


class Merchant(BaseEntity):
    """Merchant model."""
    name: str
    type: str = Field(description="FamilyMerchant or ProviderMerchant")


class Tag(BaseEntity):
    """Tag model."""
    name: str
    color: str


class Transfer(BaseModel):
    """Transfer information for transactions."""
    id: UUID
    amount: Decimal
    currency: str
    other_account: Optional[Account] = None


class Transaction(BaseEntity):
    """Transaction model."""
    date: datetime
    amount: Decimal
    currency: str
    name: str
    notes: Optional[str] = None
    classification: str
    account: Account
    category: Optional[Category] = None
    merchant: Optional[Merchant] = None
    tags: List[Tag] = Field(default_factory=list)
    transfer: Optional[Transfer] = None


class Trade(BaseEntity):
    """Trade model."""
    date: datetime
    amount: Decimal
    currency: str
    name: str
    notes: Optional[str] = None
    qty: Decimal
    price: Decimal
    investment_activity_label: Optional[str] = None
    account: Account
    security: Optional[Dict[str, Any]] = None
    category: Optional[Dict[str, Any]] = None


class Holding(BaseEntity):
    """Holding model."""
    date: datetime
    qty: Decimal = Field(description="Quantity of shares held")
    price: Decimal = Field(description="Price per share")
    amount: Decimal
    currency: str
    cost_basis_source: Optional[str] = None
    account: Account
    security: Dict[str, Any]
    avg_cost: Optional[Decimal] = None


class Valuation(BaseEntity):
    """Valuation model."""
    date: datetime
    amount: Decimal
    currency: str
    notes: Optional[str] = None
    kind: str
    account: Account


class ImportConfiguration(BaseModel):
    """Import configuration model."""
    date_col_label: Optional[str] = None
    amount_col_label: Optional[str] = None
    name_col_label: Optional[str] = None
    category_col_label: Optional[str] = None
    tags_col_label: Optional[str] = None
    notes_col_label: Optional[str] = None
    account_col_label: Optional[str] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    signage_convention: Optional[str] = None


class ImportStats(BaseModel):
    """Import statistics model."""
    rows_count: int = 0
    valid_rows_count: Optional[int] = None


class Import(BaseEntity):
    """Import model."""
    type: str
    status: ImportStatus
    account_id: Optional[UUID] = None
    rows_count: Optional[int] = None
    error: Optional[str] = None
    configuration: Optional[ImportConfiguration] = None
    stats: Optional[ImportStats] = None


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int = Field(ge=1)
    per_page: int = Field(ge=1)
    total_count: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    pagination: PaginationInfo


class TransactionCollection(PaginatedResponse):
    """Paginated transaction collection."""
    transactions: List[Transaction]


class AccountCollection(PaginatedResponse):
    """Paginated account collection."""
    accounts: List[Account]


class CategoryCollection(PaginatedResponse):
    """Paginated category collection."""
    categories: List[Category]


class TradeCollection(PaginatedResponse):
    """Paginated trade collection."""
    trades: List[Trade]


class HoldingCollection(PaginatedResponse):
    """Paginated holding collection."""
    holdings: List[Holding]


# Financial calculation models
class FinancialSummary(BaseModel):
    """Financial summary data."""
    total_cashflow: Decimal = Field(default=Decimal("0"), description="Total income")
    total_outflow: Decimal = Field(default=Decimal("0"), description="Total expenses")
    total_assets: Decimal = Field(default=Decimal("0"), description="Total asset value")
    total_liabilities: Decimal = Field(default=Decimal("0"), description="Total liability value")
    net_worth: Decimal = Field(default=Decimal("0"), description="Assets minus liabilities")
    currency: str = "USD"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AccountBalance(BaseModel):
    """Account balance information."""
    account_id: UUID
    account_name: str
    balance: Decimal
    currency: str
    classification: AccountClassification
    last_updated: datetime


class CashflowItem(BaseModel):
    """Individual cashflow item."""
    date: datetime
    amount: Decimal
    currency: str
    category: Optional[str] = None
    merchant: Optional[str] = None
    description: str
    transaction_id: UUID


class CashflowSummary(BaseModel):
    """Cashflow summary for a period."""
    period_start: datetime
    period_end: datetime
    total_income: Decimal = Field(default=Decimal("0"))
    total_expenses: Decimal = Field(default=Decimal("0"))
    net_cashflow: Decimal = Field(default=Decimal("0"))
    income_by_category: Dict[str, Decimal] = Field(default_factory=dict)
    expenses_by_category: Dict[str, Decimal] = Field(default_factory=dict)
    currency: str = "USD"


# Update Category model to avoid circular import
Category.model_rebuild()