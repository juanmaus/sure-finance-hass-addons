# Sure Finance Home Assistant Addon Documentation

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Development](#development)

## Overview

The Sure Finance Home Assistant addon integrates your Sure Finance account with Home Assistant, providing real-time financial tracking and monitoring capabilities. This addon creates sensors for various financial metrics and provides a web interface for detailed analysis.

## Features

### Financial Tracking
- **Real-time monitoring** of income, expenses, and net worth
- **Account balance tracking** for all linked accounts
- **Liability monitoring** including credit cards and loans
- **Monthly savings rate** calculation
- **Transaction categorization** and analysis

### Home Assistant Integration
- Native sensor entities for all financial metrics
- Custom Lovelace cards for data visualization
- Service calls for manual data refresh
- Configurable update intervals

### Data Management
- Intelligent caching to reduce API calls
- Local data persistence
- Automatic data synchronization
- Error recovery and retry mechanisms

## Installation

### Prerequisites
- Home Assistant OS, Supervised, or Container installation
- Sure Finance account with API access
- API key from Sure Finance (generate at https://app.sure.am/settings/api)

### Installation Steps

1. **Add Repository**
   ```
   1. Navigate to Supervisor → Add-on Store
   2. Click the three dots menu → Repositories
   3. Add: https://github.com/juanmaus/sure-finance-hass-addon
   ```

2. **Install Addon**
   ```
   1. Find "Sure Finance" in the addon store
   2. Click "Install"
   3. Wait for installation to complete
   ```

3. **Configure Addon**
   ```
   1. Click "Configuration" tab
   2. Enter your API key
   3. Adjust other settings as needed
   4. Save configuration
   ```

4. **Start Addon**
   ```
   1. Click "Start" button
   2. Check logs for any errors
   3. Navigate to Home Assistant integrations
   ```

## Configuration

### Addon Configuration

```yaml
api_key: "your-sure-finance-api-key"
host: "https://app.sure.am"  # Base URL of your Sure API; set to your local URL if self-hosted
update_interval: 300  # seconds (default: 5 minutes)
currency: "USD"      # default currency
enable_cashflow_sensor: true
enable_outflow_sensor: true
enable_liability_sensor: true
enable_account_sensors: true
enable_transaction_sensors: true
cache_duration: 3600  # seconds (default: 1 hour)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | string | required | Your Sure Finance API key |
| `update_interval` | int | 300 | How often to fetch data (seconds) |
| `currency` | string | USD | Default currency for display |
| `enable_cashflow_sensor` | bool | true | Create income tracking sensor |
| `enable_outflow_sensor` | bool | true | Create expense tracking sensor |
| `enable_liability_sensor` | bool | true | Create liability tracking sensor |
| `enable_account_sensors` | bool | true | Create individual account sensors |
| `enable_transaction_sensors` | bool | true | Enable transaction tracking |
| `cache_duration` | int | 3600 | How long to cache data (seconds) |
| `host` | string | https://app.sure.am | Base URL of the Sure API (use local URL if self-hosted) |

## Usage

### Sensors Created

The addon creates the following sensors:

#### Summary Sensors
- `sensor.sure_finance_net_worth` - Total net worth (assets - liabilities)
- `sensor.sure_finance_total_cashflow` - Total income
- `sensor.sure_finance_total_outflow` - Total expenses
- `sensor.sure_finance_total_liability` - Total liabilities
- `sensor.sure_finance_monthly_savings_rate` - Percentage of income saved

#### Account Sensors (if enabled)
- `sensor.sure_finance_account_[name]` - Balance for each account

### Sensor Attributes

Each sensor includes additional attributes:

**Net Worth Sensor:**
- `total_assets` - Sum of all asset accounts
- `total_liabilities` - Sum of all liability accounts
- `last_updated` - Last data refresh time

**Cashflow Sensor:**
- `monthly_income` - Income for current month
- `income_by_category` - Breakdown by category

**Outflow Sensor:**
- `monthly_expenses` - Expenses for current month
- `expenses_by_category` - Breakdown by category

### Lovelace Cards

#### Installing Custom Cards

1. Copy `www/lovelace-sure-finance.js` to your `www` folder
2. Add as a resource in Lovelace:
   ```yaml
   resources:
     - url: /local/lovelace-sure-finance.js
       type: module
   ```

#### Available Cards

**Summary Card:**
```yaml
type: custom:sure-finance-summary-card
entities:
  net_worth: sensor.sure_finance_net_worth
  cashflow: sensor.sure_finance_total_cashflow
  outflow: sensor.sure_finance_total_outflow
  liability: sensor.sure_finance_total_liability
  savings_rate: sensor.sure_finance_monthly_savings_rate
```

**Expense Breakdown Card:**
```yaml
type: custom:sure-finance-expense-card
entity: sensor.sure_finance_total_outflow
title: Monthly Expenses
max_items: 10
```

**Account List Card:**
```yaml
type: custom:sure-finance-accounts-card
title: Account Balances
entities:
  - sensor.sure_finance_account_checking
  - sensor.sure_finance_account_savings
  - sensor.sure_finance_account_credit_card
```

### Services

The addon provides the following services:

#### `sure_finance.refresh_data`
Manually refresh all data from the API.

```yaml
service: sure_finance.refresh_data
```

#### `sure_finance.clear_cache`
Clear all cached data.

```yaml
service: sure_finance.clear_cache
```

### Automations

**Example: Daily Summary Notification**
```yaml
automation:
  - alias: "Daily Financial Summary"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Financial Summary"
          message: >
            Net Worth: {{ states('sensor.sure_finance_net_worth') }}
            Today's Expenses: {{ state_attr('sensor.sure_finance_total_outflow', 'daily_expenses') }}
            Savings Rate: {{ states('sensor.sure_finance_monthly_savings_rate') }}%
```

**Example: High Spending Alert**
```yaml
automation:
  - alias: "High Spending Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sure_finance_total_outflow
        attribute: monthly_expenses
        above: 5000
    action:
      - service: notify.mobile_app
        data:
          title: "Spending Alert"
          message: "Monthly expenses have exceeded $5,000!"
```

## API Reference

### Data Models

#### Account
```python
class Account:
    id: UUID
    name: str
    account_type: str
    balance: Decimal
    currency: str
    classification: AccountClassification
```

#### Transaction
```python
class Transaction:
    id: UUID
    date: datetime
    amount: Decimal
    currency: str
    name: str
    classification: str
    account: Account
    category: Optional[Category]
    merchant: Optional[Merchant]
    tags: List[Tag]
```

#### FinancialSummary
```python
class FinancialSummary:
    total_cashflow: Decimal
    total_outflow: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: str
    last_updated: datetime
```

### API Client Methods

The addon uses the following API endpoints:

- `GET /api/v1/accounts` - List all accounts
- `GET /api/v1/transactions` - List transactions with filters
- `GET /api/v1/categories` - List categories
- `GET /api/v1/merchants` - List merchants
- `GET /api/v1/tags` - List tags

## Troubleshooting

### Common Issues

#### "Invalid API Key" Error
- Verify your API key is correct
- Check if the key has proper permissions
- Regenerate key if necessary

#### No Data Showing
- Check addon logs for errors
- Verify internet connectivity
- Try manual refresh service
- Clear cache and restart

#### Slow Updates
- Increase cache duration
- Check API rate limits
- Reduce update frequency

### Debug Mode

Enable debug logging:
```yaml
logger:
  default: info
  logs:
    custom_components.sure_finance: debug
```

### Log Locations
- Addon logs: Supervisor → Sure Finance → Logs
- Integration logs: Settings → System → Logs

## Development

### Project Structure
```
sure-finance/
├── config.json          # Addon configuration
├── Dockerfile           # Container definition
├── run.sh              # Startup script
├── requirements.txt    # Python dependencies
├── src/
│   ├── __init__.py
│   ├── api_client.py   # API client implementation
│   ├── models.py       # Data models
│   ├── financial_calculator.py
│   ├── cache_manager.py
│   ├── data_manager.py
│   ├── sensor.py       # HA sensor integration
│   ├── config_flow.py  # HA config flow
│   └── manifest.json   # HA manifest
├── tests/              # Test suite
├── www/                # Lovelace cards
└── docs/               # Documentation
```

### Running Tests
```bash
cd sure-finance
python -m pytest tests/ -v
```

### Building Locally
```bash
docker build -t sure-finance .
docker run -p 8099:8099 sure-finance
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- **Issues**: https://github.com/juanmaus/sure-finance-hass-addons/issues
- **Discussions**: https://github.com/juanmaus/sure-finance-hass-addons/discussions
- **Home Assistant Community**: https://community.home-assistant.io

## License

This addon is released under the MIT License. See LICENSE file for details.