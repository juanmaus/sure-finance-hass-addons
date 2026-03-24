"""Integration tests for Sure Finance addon."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api_client import SureFinanceClient
from src.cache_manager import CacheManager
from src.data_manager import DataManager
from src.financial_calculator import FinancialCalculator


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for complete addon functionality."""
    
    async def test_full_data_flow(self, tmp_path):
        """Test complete data flow from API to calculations."""
        # Create mock API client
        api_client = AsyncMock(spec=SureFinanceClient)
        
        # Mock API responses
        api_client.get_all_pages = AsyncMock(side_effect=[
            # Accounts response
            [
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
            # Transactions response
            [
                {
                    "id": str(uuid4()),
                    "date": "2024-01-15",
                    "amount": "3000.00",
                    "currency": "USD",
                    "name": "Salary",
                    "classification": "income",
                    "account": {
                        "id": str(uuid4()),
                        "name": "Checking",
                        "account_type": "checking"
                    },
                    "category": {
                        "id": str(uuid4()),
                        "name": "Salary",
                        "classification": "income",
                        "color": "#00FF00",
                        "icon": "mdi:cash"
                    },
                    "tags": []
                },
                {
                    "id": str(uuid4()),
                    "date": "2024-01-16",
                    "amount": "-200.00",
                    "currency": "USD",
                    "name": "Groceries",
                    "classification": "expense",
                    "account": {
                        "id": str(uuid4()),
                        "name": "Checking",
                        "account_type": "checking"
                    },
                    "category": {
                        "id": str(uuid4()),
                        "name": "Food",
                        "classification": "expense",
                        "color": "#FF0000",
                        "icon": "mdi:food"
                    },
                    "tags": []
                }
            ]
        ])
        
        # Create real instances
        cache_manager = CacheManager(cache_dir=tmp_path / "cache")
        calculator = FinancialCalculator(currency="USD")
        data_manager = DataManager(
            api_client=api_client,
            cache_manager=cache_manager,
            calculator=calculator,
            update_interval=300
        )
        
        # Get financial summary
        summary = await data_manager.get_financial_summary()
        
        # Verify calculations
        assert summary.total_assets == Decimal("5000")
        assert summary.total_liabilities == Decimal("1500")
        assert summary.net_worth == Decimal("3500")
        assert summary.total_cashflow == Decimal("3000")
        assert summary.total_outflow == Decimal("200")
        
        # Verify caching
        cached_summary = await data_manager.get_financial_summary()
        assert cached_summary.net_worth == summary.net_worth
        
        # API should not be called again due to cache
        assert api_client.get_all_pages.call_count == 2  # Only initial calls
    
    async def test_error_recovery(self, tmp_path):
        """Test error handling and recovery."""
        # Create mock API client that fails initially
        api_client = AsyncMock(spec=SureFinanceClient)
        api_client.get_all_pages = AsyncMock(side_effect=[
            Exception("Network error"),
            # Success on retry
            [
                {
                    "id": str(uuid4()),
                    "name": "Checking",
                    "account_type": "checking",
                    "balance": "1000.00",
                    "currency": "USD",
                    "classification": "asset"
                }
            ]
        ])
        
        cache_manager = CacheManager(cache_dir=tmp_path / "cache")
        calculator = FinancialCalculator()
        data_manager = DataManager(
            api_client=api_client,
            cache_manager=cache_manager,
            calculator=calculator
        )
        
        # First call should fail
        with pytest.raises(Exception):
            await data_manager.get_accounts()
        
        # Second call should succeed
        accounts = await data_manager.get_accounts()
        assert len(accounts) == 1
        assert accounts[0].name == "Checking"
    
    async def test_concurrent_requests(self, tmp_path):
        """Test handling of concurrent requests."""
        import asyncio
        
        # Create mock API client with delay
        api_client = AsyncMock(spec=SureFinanceClient)
        
        async def delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            return [{"id": str(uuid4()), "name": "Test", "balance": "100"}]
        
        api_client.get_all_pages = delayed_response
        
        cache_manager = CacheManager(cache_dir=tmp_path / "cache")
        calculator = FinancialCalculator()
        data_manager = DataManager(
            api_client=api_client,
            cache_manager=cache_manager,
            calculator=calculator
        )
        
        # Make concurrent requests
        results = await asyncio.gather(
            data_manager.get_accounts(),
            data_manager.get_accounts(),
            data_manager.get_accounts()
        )
        
        # All should return same data
        assert all(len(r) == 1 for r in results)
        assert all(r[0].name == "Test" for r in results)