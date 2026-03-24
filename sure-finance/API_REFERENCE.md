# Sure Finance API Client Reference

## Overview

The Sure Finance API client provides a comprehensive interface to all Sure Finance API endpoints. This document details the available methods, parameters, and response formats.

## Client Initialization

```python
from src.api_client import SureFinanceClient

# Create client instance
client = SureFinanceClient(
    api_key="your-api-key",
    base_url="https://app.sure.am",  # Optional, defaults to production
    timeout=30  # Optional, request timeout in seconds
)

# Using async context manager
async with SureFinanceClient(api_key="your-api-key") as client:
    accounts = await client.get_accounts()
```

## Authentication

All API requests require authentication via API key:
- Header: `X-Api-Key: your-api-key`
- Generate keys at: https://app.sure.am/settings/api

## Error Handling

```python
from src.api_client import APIError, AuthenticationError, RateLimitError

try:
    accounts = await client.get_accounts()
except AuthenticationError:
    # Invalid API key
    pass
except RateLimitError:
    # Rate limit exceeded
    pass
except APIError as e:
    # Other API errors
    print(f"Error: {e.message}, Status: {e.status_code}")
```

## Account Methods

### get_accounts()

Retrieve all accounts.

```python
from src.api_client import PaginationParams

# Get all accounts
accounts = await client.get_accounts()

# With pagination
accounts = await client.get_accounts(
    pagination=PaginationParams(page=1, per_page=50)
)
```

**Response:**
```python
{
    "accounts": [
        {
            "id": "uuid",
            "name": "Checking Account",
            "account_type": "checking",
            "balance": "5000.00",
            "currency": "USD",
            "classification": "asset"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 25,
        "total_count": 10,
        "total_pages": 1
    }
}
```

## Transaction Methods

### get_transactions()

Retrieve transactions with various filters.

```python
from datetime import datetime, timedelta
from src.api_client import DateRangeParams

# Get transactions for last 30 days
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)

transactions = await client.get_transactions(
    date_range=DateRangeParams(start_date=start_date, end_date=end_date),
    account_id="account-uuid",
    category_id="category-uuid",
    transaction_type="expense",  # "income" or "expense"
    search="grocery"
)
```

### get_transaction()

Retrieve a single transaction.

```python
transaction = await client.get_transaction("transaction-uuid")
```

### create_transaction()

Create a new transaction.

```python
transaction_data = {
    "account_id": "account-uuid",
    "date": "2024-01-15",
    "amount": -50.00,  # Negative for expenses
    "name": "Grocery Store",
    "category_id": "category-uuid",
    "nature": "expense"
}

transaction = await client.create_transaction(transaction_data)
```

## Category Methods

### get_categories()

Retrieve all categories.

```python
# Get all categories
categories = await client.get_categories()

# Filter by classification
categories = await client.get_categories(
    classification="expense",  # "income" or "expense"
    roots_only=True,  # Only root categories
    parent_id="parent-uuid"  # Filter by parent
)
```

### get_category()

Retrieve a single category.

```python
category = await client.get_category("category-uuid")
```

## Merchant Methods

### get_merchants()

Retrieve all merchants.

```python
merchants = await client.get_merchants()
```

### get_merchant()

Retrieve a single merchant.

```python
merchant = await client.get_merchant("merchant-uuid")
```

## Tag Methods

### get_tags()

Retrieve all tags.

```python
tags = await client.get_tags()
```

### get_tag()

Retrieve a single tag.

```python
tag = await client.get_tag("tag-uuid")
```

### create_tag()

Create a new tag.

```python
tag = await client.create_tag(
    name="Essential",
    color="#0000FF"  # Optional hex color
)
```

## Trade Methods

### get_trades()

Retrieve investment trades.

```python
trades = await client.get_trades(
    date_range=DateRangeParams(start_date=start_date, end_date=end_date),
    account_id="investment-account-uuid",
    account_ids=["account1-uuid", "account2-uuid"]  # Multiple accounts
)
```

## Holdings Methods

### get_holdings()

Retrieve investment holdings.

```python
holdings = await client.get_holdings(
    date=datetime(2024, 1, 15),  # Specific date
    account_id="investment-account-uuid",
    security_id="security-uuid"
)
```

## Valuation Methods

### create_valuation()

Create account valuation.

```python
valuation = await client.create_valuation(
    account_id="account-uuid",
    amount=10000.00,
    date=datetime.utcnow(),
    notes="Monthly valuation"
)
```

## Import Methods

### get_imports()

Retrieve import history.

```python
imports = await client.get_imports(
    status="complete",  # pending, complete, failed, etc.
    import_type="TransactionImport"
)
```

## Utility Methods

### get_all_pages()

Automatically fetch all pages of paginated data.

```python
# Get all transactions (handles pagination automatically)
all_transactions = await client.get_all_pages(
    client.get_transactions,
    per_page=100,
    date_range=date_range
)
```

## Data Models

### PaginationParams

```python
from src.api_client import PaginationParams

params = PaginationParams(
    page=1,  # Page number (default: 1)
    per_page=50  # Items per page (default: 25, max: 100)
)
```

### DateRangeParams

```python
from src.api_client import DateRangeParams

date_range = DateRangeParams(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

## Rate Limiting

The API implements rate limiting:
- Default: 1000 requests per hour
- Rate limit headers included in responses
- Automatic retry with exponential backoff

## Best Practices

1. **Use Pagination**: Always paginate large result sets
2. **Cache Results**: Implement caching for frequently accessed data
3. **Handle Errors**: Always wrap API calls in try/except blocks
4. **Close Connections**: Use context managers or explicitly close the client
5. **Batch Operations**: Use `get_all_pages()` for bulk fetching

## Example: Complete Integration

```python
import asyncio
from datetime import datetime, timedelta
from src.api_client import SureFinanceClient, PaginationParams, DateRangeParams

async def get_financial_summary():
    async with SureFinanceClient(api_key="your-api-key") as client:
        # Get all accounts
        accounts = await client.get_all_pages(client.get_accounts)
        
        # Calculate total assets and liabilities
        total_assets = sum(
            float(acc['balance']) 
            for acc in accounts 
            if acc['classification'] == 'asset'
        )
        total_liabilities = sum(
            abs(float(acc['balance'])) 
            for acc in accounts 
            if acc['classification'] == 'liability'
        )
        
        # Get recent transactions
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        transactions = await client.get_all_pages(
            client.get_transactions,
            date_range=DateRangeParams(start_date=start_date, end_date=end_date)
        )
        
        # Calculate income and expenses
        income = sum(
            float(tx['amount']) 
            for tx in transactions 
            if tx['classification'] == 'income'
        )
        expenses = sum(
            abs(float(tx['amount'])) 
            for tx in transactions 
            if tx['classification'] == 'expense'
        )
        
        return {
            "net_worth": total_assets - total_liabilities,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "monthly_income": income,
            "monthly_expenses": expenses,
            "savings_rate": (income - expenses) / income * 100 if income > 0 else 0
        }

# Run the example
if __name__ == "__main__":
    summary = asyncio.run(get_financial_summary())
    print(summary)
```