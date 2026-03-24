"""Financial calculation logic for Sure Finance addon.

This module handles all financial calculations including cashflow analysis,
liability tracking, and net worth calculations.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from .models import (
    Account,
    AccountBalance,
    AccountClassification,
    CashflowItem,
    CashflowSummary,
    FinancialSummary,
    Transaction,
    TransactionType
)

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Handles financial calculations and analysis."""
    
    def __init__(self, currency: str = "USD"):
        """Initialize calculator.
        
        Args:
            currency: Default currency for calculations
        """
        self.currency = currency
        
    def calculate_financial_summary(
        self,
        accounts: List[Account],
        transactions: Optional[List[Transaction]] = None
    ) -> FinancialSummary:
        """Calculate overall financial summary.
        
        Args:
            accounts: List of accounts
            transactions: Optional list of recent transactions
            
        Returns:
            Financial summary with totals
        """
        summary = FinancialSummary(currency=self.currency)
        
        # Calculate account totals
        for account in accounts:
            balance = Decimal(str(account.balance or 0))
            
            if account.classification == AccountClassification.ASSET:
                summary.total_assets += balance
            elif account.classification == AccountClassification.LIABILITY:
                summary.total_liabilities += abs(balance)
                
        # Calculate net worth
        summary.net_worth = summary.total_assets - summary.total_liabilities
        
        # Calculate cashflow from recent transactions if provided
        if transactions:
            for transaction in transactions:
                amount = Decimal(str(transaction.amount))
                
                if transaction.classification == TransactionType.INCOME.value:
                    summary.total_cashflow += amount
                elif transaction.classification == TransactionType.EXPENSE.value:
                    summary.total_outflow += abs(amount)
                    
        return summary
        
    def calculate_cashflow_summary(
        self,
        transactions: List[Transaction],
        period_start: datetime,
        period_end: datetime
    ) -> CashflowSummary:
        """Calculate cashflow summary for a period.
        
        Args:
            transactions: List of transactions
            period_start: Start of period
            period_end: End of period
            
        Returns:
            Cashflow summary for the period
        """
        summary = CashflowSummary(
            period_start=period_start,
            period_end=period_end,
            currency=self.currency
        )
        
        # Filter transactions by date
        period_transactions = [
            t for t in transactions
            if period_start <= t.date <= period_end
        ]
        
        # Calculate totals by category
        for transaction in period_transactions:
            amount = Decimal(str(transaction.amount))
            category_name = transaction.category.name if transaction.category else "Uncategorized"
            
            if transaction.classification == TransactionType.INCOME.value:
                summary.total_income += amount
                summary.income_by_category[category_name] = \
                    summary.income_by_category.get(category_name, Decimal("0")) + amount
            elif transaction.classification == TransactionType.EXPENSE.value:
                amount_abs = abs(amount)
                summary.total_expenses += amount_abs
                summary.expenses_by_category[category_name] = \
                    summary.expenses_by_category.get(category_name, Decimal("0")) + amount_abs
                    
        # Calculate net cashflow
        summary.net_cashflow = summary.total_income - summary.total_expenses
        
        return summary
        
    def get_account_balances(self, accounts: List[Account]) -> List[AccountBalance]:
        """Get current balance for each account.
        
        Args:
            accounts: List of accounts
            
        Returns:
            List of account balances
        """
        balances = []
        
        for account in accounts:
            balance = AccountBalance(
                account_id=account.id,
                account_name=account.name,
                balance=Decimal(str(account.balance or 0)),
                currency=account.currency or self.currency,
                classification=account.classification or AccountClassification.ASSET,
                last_updated=account.updated_at or datetime.utcnow()
            )
            balances.append(balance)
            
        return balances
        
    def get_cashflow_items(
        self,
        transactions: List[Transaction],
        transaction_type: Optional[TransactionType] = None
    ) -> List[CashflowItem]:
        """Convert transactions to cashflow items.
        
        Args:
            transactions: List of transactions
            transaction_type: Optional filter by type
            
        Returns:
            List of cashflow items
        """
        items = []
        
        for transaction in transactions:
            # Filter by type if specified
            if transaction_type:
                if transaction_type == TransactionType.INCOME and \
                   transaction.classification != TransactionType.INCOME.value:
                    continue
                elif transaction_type == TransactionType.EXPENSE and \
                     transaction.classification != TransactionType.EXPENSE.value:
                    continue
                    
            item = CashflowItem(
                date=transaction.date,
                amount=Decimal(str(transaction.amount)),
                currency=transaction.currency,
                category=transaction.category.name if transaction.category else None,
                merchant=transaction.merchant.name if transaction.merchant else None,
                description=transaction.name,
                transaction_id=transaction.id
            )
            items.append(item)
            
        return items
        
    def calculate_monthly_trends(
        self,
        transactions: List[Transaction],
        months: int = 12
    ) -> Dict[str, CashflowSummary]:
        """Calculate monthly cashflow trends.
        
        Args:
            transactions: List of transactions
            months: Number of months to analyze
            
        Returns:
            Dictionary of month -> cashflow summary
        """
        end_date = datetime.utcnow()
        trends = {}
        
        for i in range(months):
            # Calculate month boundaries
            month_end = end_date.replace(day=1) - timedelta(days=1)
            month_start = month_end.replace(day=1)
            
            # Calculate summary for the month
            month_key = month_start.strftime("%Y-%m")
            trends[month_key] = self.calculate_cashflow_summary(
                transactions,
                month_start,
                month_end
            )
            
            # Move to previous month
            end_date = month_start - timedelta(days=1)
            
        return trends
        
    def calculate_category_breakdown(
        self,
        transactions: List[Transaction],
        transaction_type: TransactionType
    ) -> Dict[str, Decimal]:
        """Calculate spending/income breakdown by category.
        
        Args:
            transactions: List of transactions
            transaction_type: Type to analyze
            
        Returns:
            Dictionary of category -> total amount
        """
        breakdown = defaultdict(Decimal)
        
        for transaction in transactions:
            if transaction_type == TransactionType.INCOME and \
               transaction.classification != TransactionType.INCOME.value:
                continue
            elif transaction_type == TransactionType.EXPENSE and \
                 transaction.classification != TransactionType.EXPENSE.value:
                continue
                
            category_name = transaction.category.name if transaction.category else "Uncategorized"
            amount = abs(Decimal(str(transaction.amount)))
            breakdown[category_name] += amount
            
        return dict(breakdown)
        
    def calculate_liability_summary(
        self,
        accounts: List[Account]
    ) -> Tuple[Decimal, List[AccountBalance]]:
        """Calculate total liabilities and list liability accounts.
        
        Args:
            accounts: List of accounts
            
        Returns:
            Tuple of (total_liabilities, liability_accounts)
        """
        total_liabilities = Decimal("0")
        liability_accounts = []
        
        for account in accounts:
            if account.classification == AccountClassification.LIABILITY:
                balance = abs(Decimal(str(account.balance or 0)))
                total_liabilities += balance
                
                liability_accounts.append(AccountBalance(
                    account_id=account.id,
                    account_name=account.name,
                    balance=balance,
                    currency=account.currency or self.currency,
                    classification=AccountClassification.LIABILITY,
                    last_updated=account.updated_at or datetime.utcnow()
                ))
                
        return total_liabilities, liability_accounts
        
    def calculate_savings_rate(
        self,
        income: Decimal,
        expenses: Decimal
    ) -> Decimal:
        """Calculate savings rate as percentage.
        
        Args:
            income: Total income
            expenses: Total expenses
            
        Returns:
            Savings rate as percentage (0-100)
        """
        if income <= 0:
            return Decimal("0")
            
        savings = income - expenses
        rate = (savings / income) * 100
        
        # Ensure rate is between 0 and 100
        return max(Decimal("0"), min(Decimal("100"), rate))
        
    def detect_recurring_transactions(
        self,
        transactions: List[Transaction],
        threshold_days: int = 35
    ) -> Dict[str, List[Transaction]]:
        """Detect potentially recurring transactions.
        
        Args:
            transactions: List of transactions
            threshold_days: Max days between recurring transactions
            
        Returns:
            Dictionary grouping similar recurring transactions
        """
        # Group by merchant and similar amounts
        grouped = defaultdict(list)
        
        for transaction in transactions:
            if transaction.merchant:
                # Create key from merchant and rounded amount
                amount_rounded = round(Decimal(str(transaction.amount)), 0)
                key = f"{transaction.merchant.name}_{amount_rounded}"
                grouped[key].append(transaction)
                
        # Filter to only groups with multiple transactions
        recurring = {}
        for key, trans_list in grouped.items():
            if len(trans_list) >= 2:
                # Sort by date
                trans_list.sort(key=lambda t: t.date)
                
                # Check if transactions are roughly periodic
                is_recurring = True
                for i in range(1, len(trans_list)):
                    days_diff = (trans_list[i].date - trans_list[i-1].date).days
                    if days_diff > threshold_days:
                        is_recurring = False
                        break
                        
                if is_recurring:
                    recurring[key] = trans_list
                    
        return recurring