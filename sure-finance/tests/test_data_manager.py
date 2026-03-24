"""Tests for data manager."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.data_manager import DataManager
from src.api_client import SureFinanceClient
from src.cache_manager import CacheManager
from src.financial_calculator import FinancialCalculator
from src.models import (
    Account,
    Transaction,
    Category,
    Merchant,
    Tag,
    FinancialSummary,
    CashflowSummary
)


@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    client = AsyncMock(spec=SureFinanceClient)
    client.get_all_pages = AsyncMock()
    client.get_accounts = AsyncMock()
    client.get_transactions = AsyncMock()
    client.get_categories = AsyncMock()
    client.get_merchants = AsyncMock()
    client.get_tags = AsyncMock()
    return client


@pytest.fixture
def mock_cache_manager():
    """Create mock cache manager."""
    manager = AsyncMock(spec=CacheManager)
    manager.get = AsyncMock(return_value=None)
    manager.set = AsyncMock()
    manager.account_key = MagicMock(return_value="accounts:all")
    manager.transaction_key = MagicMock(return_value="transactions:all")
    manager.summary_key = MagicMock(return_value="summary:current")
    manager.cashflow_key = MagicMock(return_value="cashflow:2024-01")
    manager.cleanup_expired = MagicMock()
    return manager


@pytest.fixture
def calculator():
    """Create financial calculator."""
    return FinancialCalculator()


@pytest.fixture
def data_manager(mock_api_client, mock_cache_manager, calculator):
    """Create data manager instance."""
    return DataManager(
        api_client=mock_api_client,
        cache_manager=mock_cache_manager,
        calculator=calculator,
        update_interval=300
    )


@pytest.fixture
def sample_api_data():
    """Create sample API response data."""
    return {
        "accounts": [
            {
                "id": str(uuid4()),
                "name": "Checking",
                "account_type": "checking",
                "balance": "5000.00",
                "currency": "USD",
                "classification": "asset"
            },
            {
                "id": str(uuid4()),
                "name": "Credit Card",
                "account_type": "credit",
                "balance": "-1500.00",
                "currency": "USD",
                "classification": "liability"
            }
        ],
        "transactions": [
            {
                "id": str(uuid4()),
                "date": "2024-01-15",
                "amount": "100.00",
                "currency": "USD",
                "name": "Grocery Store",
                "classification": "expense",
                "account": {
                    "id": str(uuid4()),
                    "name": "Checking",
                    "account_type": "checking"
                },
                "tags": []
            }
        ],
        "categories": [
            {
                "id": str(uuid4()),
                "name": "Groceries",
                "classification": "expense",
                "color": "#FF0000",
                "icon": "mdi:cart"
            }
        ],
        "merchants": [
            {
                "id": str(uuid4()),
                "name": "Grocery Store",
                "type": "ProviderMerchant"
            }
        ],
        "tags": [
            {
                "id": str(uuid4()),
                "name": "Essential",
                "color": "#0000FF"
            }
        ]
    }


class TestDataManager:
    """Test data manager."""
    
    @pytest.mark.asyncio
    async def test_get_accounts_from_api(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test getting accounts from API."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["accounts"]
        mock_cache_manager.get.return_value = None  # No cache
        
        # Execute
        accounts = await data_manager.get_accounts()
        
        # Verify
        assert len(accounts) == 2
        assert isinstance(accounts[0], Account)
        assert accounts[0].name == "Checking"
        assert accounts[1].name == "Credit Card"
        
        # Check API called
        mock_api_client.get_all_pages.assert_called_once()
        
        # Check cache set
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_accounts_from_cache(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test getting accounts from cache."""
        # Setup - return cached data
        mock_cache_manager.get.return_value = sample_api_data["accounts"]
        
        # Execute
        accounts = await data_manager.get_accounts()
        
        # Verify
        assert len(accounts) == 2
        assert accounts[0].name == "Checking"
        
        # Check API not called
        mock_api_client.get_all_pages.assert_not_called()
        
        # Check cache not set again
        mock_cache_manager.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_accounts_force_refresh(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test forcing account refresh."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["accounts"]
        mock_cache_manager.get.return_value = [{"id": "old", "name": "Old Account"}]
        
        # Execute with force refresh
        accounts = await data_manager.get_accounts(force_refresh=True)
        
        # Verify API was called despite cache
        mock_api_client.get_all_pages.assert_called_once()
        assert accounts[0].name == "Checking"
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test getting transactions."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["transactions"]
        mock_cache_manager.get.return_value = None
        
        # Execute
        transactions = await data_manager.get_transactions(days=30)
        
        # Verify
        assert len(transactions) == 1
        assert isinstance(transactions[0], Transaction)
        assert transactions[0].name == "Grocery Store"
        
        # Check date range was passed
        call_args = mock_api_client.get_all_pages.call_args
        assert "date_range" in call_args[1]
        date_range = call_args[1]["date_range"]
        assert (date_range.end_date - date_range.start_date).days == 30
    
    @pytest.mark.asyncio
    async def test_get_financial_summary(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test getting financial summary."""
        # Setup
        mock_api_client.get_all_pages.side_effect = [
            sample_api_data["accounts"],  # For get_accounts
            sample_api_data["transactions"]  # For get_transactions
        ]
        mock_cache_manager.get.return_value = None
        
        # Execute
        summary = await data_manager.get_financial_summary()
        
        # Verify
        assert isinstance(summary, FinancialSummary)
        assert summary.currency == "USD"
        
        # Check cache was set for summary
        cache_calls = [call for call in mock_cache_manager.set.call_args_list
                      if "summary" in str(call)]
        assert len(cache_calls) > 0
    
    @pytest.mark.asyncio
    async def test_get_monthly_cashflow(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test getting monthly cashflow."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["transactions"]
        mock_cache_manager.get.return_value = None
        
        # Execute
        cashflow = await data_manager.get_monthly_cashflow(2024, 1)
        
        # Verify
        assert isinstance(cashflow, CashflowSummary)
        assert cashflow.period_start.year == 2024
        assert cashflow.period_start.month == 1
        
        # Check date range
        call_args = mock_api_client.get_all_pages.call_args
        date_range = call_args[1]["date_range"]
        assert date_range.start_date.day == 1
        assert date_range.end_date.day == 31
    
    @pytest.mark.asyncio
    async def test_sync_all_data(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test syncing all data."""
        # Setup
        mock_api_client.get_all_pages.side_effect = [
            sample_api_data["accounts"],
            sample_api_data["categories"],
            sample_api_data["merchants"],
            sample_api_data["tags"],
            sample_api_data["transactions"],
            sample_api_data["accounts"],  # For financial summary
            sample_api_data["transactions"]  # For financial summary
        ]
        mock_api_client.get_merchants.return_value = sample_api_data["merchants"]
        mock_api_client.get_tags.return_value = sample_api_data["tags"]
        
        # Execute
        await data_manager.sync_all_data()
        
        # Verify all data types were fetched
        assert mock_api_client.get_all_pages.call_count >= 5
        assert mock_api_client.get_merchants.called
        assert mock_api_client.get_tags.called
    
    def test_needs_update(self, data_manager):
        """Test update check logic."""
        # No last update - needs update
        assert data_manager.needs_update("accounts") is True
        
        # Set last update to now
        data_manager._last_updates["accounts"] = datetime.utcnow()
        assert data_manager.needs_update("accounts") is False
        
        # Set last update to past
        data_manager._last_updates["accounts"] = datetime.utcnow() - timedelta(seconds=400)
        assert data_manager.needs_update("accounts") is True
    
    @pytest.mark.asyncio
    async def test_periodic_sync(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test periodic sync task."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["accounts"]
        data_manager.update_interval = 0.1  # Very short for testing
        
        # Start periodic sync
        task = asyncio.create_task(data_manager.periodic_sync())
        
        # Wait a bit
        await asyncio.sleep(0.2)
        
        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify sync was called
        assert mock_api_client.get_all_pages.call_count > 0
        assert mock_cache_manager.cleanup_expired.called
    
    @pytest.mark.asyncio
    async def test_error_handling_with_cache_fallback(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test error handling with cache fallback."""
        # Setup - API fails but cache has data
        mock_api_client.get_all_pages.side_effect = Exception("API Error")
        mock_cache_manager.get.return_value = sample_api_data["accounts"]
        
        # Execute
        accounts = await data_manager.get_accounts()
        
        # Verify fallback to cache
        assert len(accounts) == 2
        assert accounts[0].name == "Checking"
    
    @pytest.mark.asyncio
    async def test_get_categories_with_long_cache(self, data_manager, mock_api_client, mock_cache_manager, sample_api_data):
        """Test categories are cached for longer."""
        # Setup
        mock_api_client.get_all_pages.return_value = sample_api_data["categories"]
        mock_cache_manager.get.return_value = None
        
        # Execute
        categories = await data_manager.get_categories()
        
        # Verify
        assert len(categories) == 1
        
        # Check cache TTL is 24 hours
        cache_call = mock_cache_manager.set.call_args
        assert cache_call[1]["ttl"] == 86400  # 24 hours