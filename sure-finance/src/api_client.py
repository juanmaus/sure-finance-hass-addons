"""Sure Finance API Client.

This module provides a comprehensive client for interacting with the Sure Finance API.
It handles authentication, request management, and provides methods for all API endpoints.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from pydantic import BaseModel, Field, ConfigDict

# Configure logging
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)


class DateRangeParams(BaseModel):
    """Date range parameters for filtering."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SureFinanceClient:
    """Async client for Sure Finance API."""
    
    BASE_URL = "https://app.sure.am"
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize the API client.
        
        Args:
            api_key: Sure Finance API key
            base_url: Optional custom base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = ClientTimeout(total=timeout or self.DEFAULT_TIMEOUT)
        self._session: Optional[ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def connect(self):
        """Create aiohttp session."""
        if not self._session:
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            self._session = ClientSession(
                headers=headers,
                timeout=self.timeout
            )
            
    async def close(self):
        """Close aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
            
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for endpoint."""
        return urljoin(self.base_url, endpoint)
        
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIError: For API errors
            AuthenticationError: For auth failures
            RateLimitError: For rate limit errors
        """
        if not self._session:
            await self.connect()
            
        url = self._build_url(endpoint)
        
        try:
            async with self._session.request(method, url, **kwargs) as response:
                data = await response.json() if response.content_length else {}
                
                if response.status == 200 or response.status == 201:
                    return data
                elif response.status == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        status_code=401,
                        details=data
                    )
                elif response.status == 429:
                    raise RateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        details=data
                    )
                else:
                    error_msg = data.get("error", "Unknown error")
                    raise APIError(
                        f"API error: {error_msg}",
                        status_code=response.status,
                        details=data
                    )
                    
        except aiohttp.ClientError as e:
            raise APIError(f"Network error: {str(e)}")
            
    # Account endpoints
    async def get_accounts(self, pagination: Optional[PaginationParams] = None) -> Dict[str, Any]:
        """Get list of accounts.
        
        Args:
            pagination: Pagination parameters
            
        Returns:
            Account collection with pagination
        """
        params = {}
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        return await self._request("GET", "/api/v1/accounts", params=params)
        
    # Transaction endpoints
    async def get_transactions(
        self,
        pagination: Optional[PaginationParams] = None,
        date_range: Optional[DateRangeParams] = None,
        account_id: Optional[str] = None,
        category_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of transactions with filters.
        
        Args:
            pagination: Pagination parameters
            date_range: Date range filter
            account_id: Filter by account
            category_id: Filter by category
            merchant_id: Filter by merchant
            transaction_type: Filter by type (income/expense)
            search: Search query
            
        Returns:
            Transaction collection with pagination
        """
        params = {}
        
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        if date_range:
            if date_range.start_date:
                params["start_date"] = date_range.start_date.strftime("%Y-%m-%d")
            if date_range.end_date:
                params["end_date"] = date_range.end_date.strftime("%Y-%m-%d")
                
        if account_id:
            params["account_id"] = account_id
        if category_id:
            params["category_id"] = category_id
        if merchant_id:
            params["merchant_id"] = merchant_id
        if transaction_type:
            params["type"] = transaction_type
        if search:
            params["search"] = search
            
        return await self._request("GET", "/api/v1/transactions", params=params)
        
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get single transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction details
        """
        return await self._request("GET", f"/api/v1/transactions/{transaction_id}")
        
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new transaction.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            Created transaction
        """
        return await self._request(
            "POST",
            "/api/v1/transactions",
            json={"transaction": transaction_data}
        )
        
    # Category endpoints
    async def get_categories(
        self,
        pagination: Optional[PaginationParams] = None,
        classification: Optional[str] = None,
        roots_only: bool = False,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of categories.
        
        Args:
            pagination: Pagination parameters
            classification: Filter by classification (income/expense)
            roots_only: Return only root categories
            parent_id: Filter by parent category
            
        Returns:
            Category collection with pagination
        """
        params = {}
        
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        if classification:
            params["classification"] = classification
        if roots_only:
            params["roots_only"] = "true"
        if parent_id:
            params["parent_id"] = parent_id
            
        return await self._request("GET", "/api/v1/categories", params=params)
        
    async def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get single category by ID.
        
        Args:
            category_id: Category ID
            
        Returns:
            Category details
        """
        return await self._request("GET", f"/api/v1/categories/{category_id}")
        
    # Merchant endpoints
    async def get_merchants(self) -> List[Dict[str, Any]]:
        """Get list of merchants.
        
        Returns:
            List of merchant details
        """
        return await self._request("GET", "/api/v1/merchants")
        
    async def get_merchant(self, merchant_id: str) -> Dict[str, Any]:
        """Get single merchant by ID.
        
        Args:
            merchant_id: Merchant ID
            
        Returns:
            Merchant details
        """
        return await self._request("GET", f"/api/v1/merchants/{merchant_id}")
        
    # Tag endpoints
    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get list of tags.
        
        Returns:
            List of tag details
        """
        return await self._request("GET", "/api/v1/tags")
        
    async def get_tag(self, tag_id: str) -> Dict[str, Any]:
        """Get single tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag details
        """
        return await self._request("GET", f"/api/v1/tags/{tag_id}")
        
    async def create_tag(self, name: str, color: Optional[str] = None) -> Dict[str, Any]:
        """Create new tag.
        
        Args:
            name: Tag name
            color: Optional hex color
            
        Returns:
            Created tag
        """
        tag_data = {"name": name}
        if color:
            tag_data["color"] = color
            
        return await self._request(
            "POST",
            "/api/v1/tags",
            json={"tag": tag_data}
        )
        
    # Trade endpoints
    async def get_trades(
        self,
        pagination: Optional[PaginationParams] = None,
        date_range: Optional[DateRangeParams] = None,
        account_id: Optional[str] = None,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get list of trades.
        
        Args:
            pagination: Pagination parameters
            date_range: Date range filter
            account_id: Filter by single account
            account_ids: Filter by multiple accounts
            
        Returns:
            Trade collection with pagination
        """
        params = {}
        
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        if date_range:
            if date_range.start_date:
                params["start_date"] = date_range.start_date.strftime("%Y-%m-%d")
            if date_range.end_date:
                params["end_date"] = date_range.end_date.strftime("%Y-%m-%d")
                
        if account_id:
            params["account_id"] = account_id
        if account_ids:
            params["account_ids"] = account_ids
            
        return await self._request("GET", "/api/v1/trades", params=params)
        
    # Holdings endpoints
    async def get_holdings(
        self,
        pagination: Optional[PaginationParams] = None,
        date: Optional[datetime] = None,
        date_range: Optional[DateRangeParams] = None,
        account_id: Optional[str] = None,
        account_ids: Optional[List[str]] = None,
        security_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of holdings.
        
        Args:
            pagination: Pagination parameters
            date: Filter by exact date
            date_range: Date range filter
            account_id: Filter by single account
            account_ids: Filter by multiple accounts
            security_id: Filter by security
            
        Returns:
            Holding collection with pagination
        """
        params = {}
        
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        if date:
            params["date"] = date.strftime("%Y-%m-%d")
        elif date_range:
            if date_range.start_date:
                params["start_date"] = date_range.start_date.strftime("%Y-%m-%d")
            if date_range.end_date:
                params["end_date"] = date_range.end_date.strftime("%Y-%m-%d")
                
        if account_id:
            params["account_id"] = account_id
        if account_ids:
            params["account_ids"] = account_ids
        if security_id:
            params["security_id"] = security_id
            
        return await self._request("GET", "/api/v1/holdings", params=params)
        
    # Valuation endpoints
    async def create_valuation(
        self,
        account_id: str,
        amount: float,
        date: datetime,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new valuation.
        
        Args:
            account_id: Account ID
            amount: Valuation amount
            date: Valuation date
            notes: Optional notes
            
        Returns:
            Created valuation
        """
        valuation_data = {
            "account_id": account_id,
            "amount": amount,
            "date": date.strftime("%Y-%m-%d")
        }
        if notes:
            valuation_data["notes"] = notes
            
        return await self._request(
            "POST",
            "/api/v1/valuations",
            json={"valuation": valuation_data}
        )
        
    # Import endpoints
    async def get_imports(
        self,
        pagination: Optional[PaginationParams] = None,
        status: Optional[str] = None,
        import_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of imports.
        
        Args:
            pagination: Pagination parameters
            status: Filter by status
            import_type: Filter by type
            
        Returns:
            Import collection with pagination
        """
        params = {}
        
        if pagination:
            params.update(pagination.model_dump(exclude_none=True))
            
        if status:
            params["status"] = status
        if import_type:
            params["type"] = import_type
            
        return await self._request("GET", "/api/v1/imports", params=params)
        
    # Utility methods
    async def get_all_pages(
        self,
        endpoint_func,
        per_page: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get all pages of paginated data.
        
        Args:
            endpoint_func: Async function to call
            per_page: Items per page
            **kwargs: Additional parameters for endpoint
            
        Returns:
            Combined list of all items
        """
        all_items = []
        page = 1
        
        while True:
            pagination = PaginationParams(page=page, per_page=per_page)
            result = await endpoint_func(pagination=pagination, **kwargs)
            
            # Extract items based on response structure
            if "transactions" in result:
                items = result["transactions"]
            elif "accounts" in result:
                items = result["accounts"]
            elif "categories" in result:
                items = result["categories"]
            elif "trades" in result:
                items = result["trades"]
            elif "holdings" in result:
                items = result["holdings"]
            elif "data" in result:
                items = result["data"]
            else:
                break
                
            all_items.extend(items)
            
            # Check if more pages exist
            pagination_info = result.get("pagination") or result.get("meta")
            if not pagination_info:
                break
                
            total_pages = pagination_info.get("total_pages", 0)
            if page >= total_pages:
                break
                
            page += 1
            
        return all_items