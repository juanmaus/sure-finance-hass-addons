# Sure Finance Home Assistant Addon

Track your financial data from Sure Finance directly in Home Assistant. This addon provides real-time monitoring of cashflows, outflows, and liabilities.

## Features

- **Real-time Financial Tracking**: Monitor income, expenses, and liabilities
- **Multiple Sensors**: Separate sensors for different financial metrics
- **Account Integration**: Track individual account balances and transactions
- **Configurable Updates**: Set your preferred update interval
- **Data Caching**: Reduce API calls with intelligent caching
- **Web Dashboard**: Built-in web interface for detailed views
- **Home Assistant Integration**: Native sensors and entities

## Installation

1. Add this repository to your Home Assistant addon store
2. Install the Sure Finance addon
3. Configure your API key from Sure Finance
4. Start the addon

## Configuration

- `api_key`: Your Sure Finance API key (required)
- `update_interval`: How often to fetch data (seconds, default: 300)
- `currency`: Default currency for display (default: USD)
- `enable_cashflow_sensor`: Enable income tracking sensor
- `enable_outflow_sensor`: Enable expense tracking sensor
- `enable_liability_sensor`: Enable liability tracking sensor
- `enable_account_sensors`: Create sensors for each account
- `enable_transaction_sensors`: Enable transaction tracking
- `cache_duration`: How long to cache data (seconds, default: 3600)

## Sensors Created

- `sensor.sure_finance_total_cashflow`: Total income
- `sensor.sure_finance_total_outflow`: Total expenses
- `sensor.sure_finance_total_liability`: Total liabilities
- `sensor.sure_finance_net_worth`: Calculated net worth
- `sensor.sure_finance_account_[name]`: Individual account balances

## Support

For issues and feature requests, please visit the GitHub repository.