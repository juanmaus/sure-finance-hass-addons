"""Tests for Sure Finance API client."""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp
from aiohttp import ClientSession

from src.api_client import (
    SureFinanceClient,
    APIError,
    AuthenticationError,
    RateLimitError,
    PaginationParams,
    DateRangeParams
)


@pytest.fixture
async def api_client():
    """Create API client instance."""
    client = SureFinanceClient(api_key="test_api_key")
    yield client
    await client.close()


@pytest.fixture
def mock_response():
    """Create mock response."""
    mock = AsyncMock()
    mock.status = 200
    mock.content_length = 1
    mock.json = AsyncMock(return_value={"test": "data"})
    return mock


class TestSureFinanceClient:
    """Test Sure Finance API client."""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test client initialization."""
        client = SureFinanceClient(
            api_key="test_key",
            base_url="https://custom.url",
            timeout=60
        )
        assert client.api_key == "test_key"
        assert client.base_url == "https://custom.url"
        assert client.timeout.total == 60
        await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, api_client):
        """Test async context manager."""
        async with SureFinanceClient(api_key="test") as client:
            assert client._session is not None
            assert isinstance(client._session, ClientSession)
    
    @pytest.mark.asyncio
    async def test_connect(self, api_client):
        """Test session creation."""
        await api_client.connect()
        assert api_client._session is not None
        assert "X-Api-Key" in api_client._session.headers
        assert api_client._session.headers["X-Api-Key"] == "test_api_key"
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, api_client, mock_response):
        """Test authentication error handling."""
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={"error": "Invalid API key"})
        
        with patch.object(api_client, "_session") as mock_session:
            mock_session.request = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(AuthenticationError) as exc_info:
                await api_client._request("GET", "/test")
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, api_client, mock_response):
        """Test rate limit error handling."""
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"error": "Rate limit exceeded"})
        
        with patch.object(api_client, "_session") as mock_session:
            mock_session.request = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(RateLimitError) as exc_info:
                await api_client._request("GET", "/test")
            
            assert exc_info.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, api_client, mock_response):
        """Test getting accounts."""
        mock_response.json = AsyncMock(return_value={
            "accounts": [
                {
                    "id": "123",
                    "name": "Checking",
                    "balance": "1000.00",
                    "currency": "USD"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 25,
                "total_count": 1,
                "total_pages": 1
            }
        })
        
        with patch.object(api_client, "_request", return_value=mock_response.json.return_value):
            result = await api_client.get_accounts()
            
            assert "accounts" in result
            assert len(result["accounts"]) == 1
            assert result["accounts"][0]["name"] == "Checking"
    
    @pytest.mark.asyncio
    async def test_get_transactions_with_filters(self, api_client):
        """Test getting transactions with filters."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        date_range = DateRangeParams(start_date=start_date, end_date=end_date)
        
        with patch.object(api_client, "_request") as mock_request:
            await api_client.get_transactions(
                pagination=PaginationParams(page=1, per_page=50),
                date_range=date_range,
                account_id="123",
                transaction_type="expense"
            )
            
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            params = call_args[1]["params"]
            
            assert params["page"] == 1
            assert params["per_page"] == 50
            assert params["account_id"] == "123"
            assert params["type"] == "expense"
            assert "start_date" in params
            assert "end_date" in params
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, api_client):
        """Test creating a transaction."""
        transaction_data = {
            "account_id": "123",
            "date": "2024-01-01",
            "amount": 50.00,
            "name": "Test Transaction"
        }
        
        with patch.object(api_client, "_request") as mock_request:
            await api_client.create_transaction(transaction_data)
            
            mock_request.assert_called_once_with(
                "POST",
                "/api/v1/transactions",
                json={"transaction": transaction_data}
            )
    
    @pytest.mark.asyncio
    async def test_get_all_pages(self, api_client):
        """Test pagination handling."""
        # Mock responses for 3 pages
        page1 = {
            "accounts": [{"id": "1"}, {"id": "2"}],
            "pagination": {"page": 1, "total_pages": 3}
        }
        page2 = {
            "accounts": [{"id": "3"}, {"id": "4"}],
            "pagination": {"page": 2, "total_pages": 3}
        }
        page3 = {
            "accounts": [{"id": "5"}],
            "pagination": {"page": 3, "total_pages": 3}
        }
        
        async def mock_get_accounts(pagination=None, **kwargs):
            if pagination.page == 1:
                return page1
            elif pagination.page == 2:
                return page2
            else:
                return page3
        
        api_client.get_accounts = mock_get_accounts
        
        result = await api_client.get_all_pages(
            api_client.get_accounts,
            per_page=2
        )
        
        assert len(result) == 5
        assert result[0]["id"] == "1"
        assert result[4]["id"] == "5"


class TestPaginationParams:
    """Test pagination parameters."""
    
    def test_defaults(self):
        """Test default values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 25
    
    def test_validation(self):
        """Test parameter validation."""
        with pytest.raises(ValueError):
            PaginationParams(page=0)
        
        with pytest.raises(ValueError):
            PaginationParams(per_page=101)


class TestDateRangeParams:
    """Test date range parameters."""
    
    def test_optional_dates(self):
        """Test optional date parameters."""
        params = DateRangeParams()
        assert params.start_date is None
        assert params.end_date is None
    
    def test_with_dates(self):
        """Test with date values."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        params = DateRangeParams(start_date=start, end_date=end)
        assert params.start_date == start
        assert params.end_date == end