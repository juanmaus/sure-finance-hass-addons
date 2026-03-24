"""Tests for financial calculator."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.financial_calculator import FinancialCalculator
from src.models import (
    Account,
    AccountClassification,
    Transaction,
    TransactionType,
    Category,
    CategoryClassification,
    Merchant,
    FinancialSummary,
    CashflowSummary
)


@pytest.fixture
def calculator():
    """Create calculator instance."""
    return FinancialCalculator(currency="USD")


@pytest.fixture
def sample_accounts():
    """Create sample accounts."""
    return [
        Account(
            id=uuid4(),
            name="Checking",
            account_type="checking",
            balance=Decimal("5000"),
            currency="USD",
            classification=AccountClassification.ASSET
        ),
        Account(
            id=uuid4(),
            name="Savings",
            account_type="savings",
            balance=Decimal("10000"),
            currency="USD",
            classification=AccountClassification.ASSET
        ),
        Account(
            id=uuid4(),
            name="Credit Card",
            account_type="credit",
            balance=Decimal("-2000"),
            currency="USD",
            classification=AccountClassification.LIABILITY
        ),
        Account(
            id=uuid4(),
            name="Mortgage",
            account_type="loan",
            balance=Decimal("-150000"),
            currency="USD",
            classification=AccountClassification.LIABILITY
        )
    ]


@pytest.fixture
def sample_transactions(sample_accounts):
    """Create sample transactions."""
    income_category = Category(
        id=uuid4(),
        name="Salary",
        classification=CategoryClassification.INCOME,
        color="#00FF00",
        icon="mdi:cash"
    )
    
    expense_category = Category(
        id=uuid4(),
        name="Groceries",
        classification=CategoryClassification.EXPENSE,
        color="#FF0000",
        icon="mdi:cart"
    )
    
    return [
        Transaction(
            id=uuid4(),
            date=datetime.utcnow(),
            amount=Decimal("5000"),
            currency="USD",
            name="Monthly Salary",
            classification=TransactionType.INCOME.value,
            account=sample_accounts[0],
            category=income_category
        ),
        Transaction(
            id=uuid4(),
            date=datetime.utcnow(),
            amount=Decimal("-200"),
            currency="USD",
            name="Grocery Shopping",
            classification=TransactionType.EXPENSE.value,
            account=sample_accounts[0],
            category=expense_category
        ),
        Transaction(
            id=uuid4(),
            date=datetime.utcnow() - timedelta(days=5),
            amount=Decimal("-150"),
            currency="USD",
            name="Restaurant",
            classification=TransactionType.EXPENSE.value,
            account=sample_accounts[2],
            category=expense_category
        )
    ]


class TestFinancialCalculator:
    """Test financial calculator."""
    
    def test_calculate_financial_summary(self, calculator, sample_accounts, sample_transactions):
        """Test financial summary calculation."""
        summary = calculator.calculate_financial_summary(
            sample_accounts,
            sample_transactions
        )
        
        assert summary.total_assets == Decimal("15000")  # 5000 + 10000
        assert summary.total_liabilities == Decimal("152000")  # 2000 + 150000
        assert summary.net_worth == Decimal("-137000")  # 15000 - 152000
        assert summary.total_cashflow == Decimal("5000")  # Income
        assert summary.total_outflow == Decimal("350")  # 200 + 150
        assert summary.currency == "USD"
    
    def test_calculate_cashflow_summary(self, calculator, sample_transactions):
        """Test cashflow summary calculation."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        summary = calculator.calculate_cashflow_summary(
            sample_transactions,
            start_date,
            end_date
        )
        
        assert summary.total_income == Decimal("5000")
        assert summary.total_expenses == Decimal("350")
        assert summary.net_cashflow == Decimal("4650")
        assert "Salary" in summary.income_by_category
        assert "Groceries" in summary.expenses_by_category
        assert summary.income_by_category["Salary"] == Decimal("5000")
        assert summary.expenses_by_category["Groceries"] == Decimal("350")
    
    def test_get_account_balances(self, calculator, sample_accounts):
        """Test getting account balances."""
        balances = calculator.get_account_balances(sample_accounts)
        
        assert len(balances) == 4
        assert balances[0].account_name == "Checking"
        assert balances[0].balance == Decimal("5000")
        assert balances[0].classification == AccountClassification.ASSET
        
        assert balances[2].account_name == "Credit Card"
        assert balances[2].balance == Decimal("-2000")
        assert balances[2].classification == AccountClassification.LIABILITY
    
    def test_calculate_savings_rate(self, calculator):
        """Test savings rate calculation."""
        # Normal case
        rate = calculator.calculate_savings_rate(
            income=Decimal("5000"),
            expenses=Decimal("3000")
        )
        assert rate == Decimal("40")  # (5000-3000)/5000 * 100
        
        # No income
        rate = calculator.calculate_savings_rate(
            income=Decimal("0"),
            expenses=Decimal("100")
        )
        assert rate == Decimal("0")
        
        # Expenses exceed income
        rate = calculator.calculate_savings_rate(
            income=Decimal("1000"),
            expenses=Decimal("1500")
        )
        assert rate == Decimal("0")
        
        # No expenses
        rate = calculator.calculate_savings_rate(
            income=Decimal("1000"),
            expenses=Decimal("0")
        )
        assert rate == Decimal("100")
    
    def test_calculate_liability_summary(self, calculator, sample_accounts):
        """Test liability summary calculation."""
        total, liability_accounts = calculator.calculate_liability_summary(sample_accounts)
        
        assert total == Decimal("152000")
        assert len(liability_accounts) == 2
        assert liability_accounts[0].account_name == "Credit Card"
        assert liability_accounts[0].balance == Decimal("2000")  # Absolute value
        assert liability_accounts[1].account_name == "Mortgage"
        assert liability_accounts[1].balance == Decimal("150000")
    
    def test_calculate_category_breakdown(self, calculator, sample_transactions):
        """Test category breakdown calculation."""
        # Expense breakdown
        expense_breakdown = calculator.calculate_category_breakdown(
            sample_transactions,
            TransactionType.EXPENSE
        )
        
        assert "Groceries" in expense_breakdown
        assert expense_breakdown["Groceries"] == Decimal("350")
        
        # Income breakdown
        income_breakdown = calculator.calculate_category_breakdown(
            sample_transactions,
            TransactionType.INCOME
        )
        
        assert "Salary" in income_breakdown
        assert income_breakdown["Salary"] == Decimal("5000")
    
    def test_calculate_monthly_trends(self, calculator, sample_transactions):
        """Test monthly trend calculation."""
        # Add transactions from different months
        transactions = list(sample_transactions)
        
        # Add transaction from last month
        last_month = datetime.utcnow() - timedelta(days=35)
        transactions.append(
            Transaction(
                id=uuid4(),
                date=last_month,
                amount=Decimal("3000"),
                currency="USD",
                name="Last Month Salary",
                classification=TransactionType.INCOME.value,
                account=sample_accounts[0],
                category=Category(
                    id=uuid4(),
                    name="Salary",
                    classification=CategoryClassification.INCOME,
                    color="#00FF00",
                    icon="mdi:cash"
                )
            )
        )
        
        trends = calculator.calculate_monthly_trends(transactions, months=3)
        
        assert len(trends) <= 3
        for month_key, summary in trends.items():
            assert isinstance(summary, CashflowSummary)
            assert summary.total_income >= 0
            assert summary.total_expenses >= 0
    
    def test_detect_recurring_transactions(self, calculator, sample_accounts):
        """Test recurring transaction detection."""
        merchant = Merchant(
            id=uuid4(),
            name="Netflix",
            type="ProviderMerchant"
        )
        
        # Create recurring transactions
        transactions = []
        for i in range(3):
            date = datetime.utcnow() - timedelta(days=30 * i)
            transactions.append(
                Transaction(
                    id=uuid4(),
                    date=date,
                    amount=Decimal("-15.99"),
                    currency="USD",
                    name="Netflix Subscription",
                    classification=TransactionType.EXPENSE.value,
                    account=sample_accounts[0],
                    merchant=merchant
                )
            )
        
        recurring = calculator.detect_recurring_transactions(transactions)
        
        assert len(recurring) == 1
        assert "Netflix_-16" in recurring
        assert len(recurring["Netflix_-16"]) == 3