#!/usr/bin/with-contenv bashio

# Get configuration from Home Assistant
export API_KEY=$(bashio::config 'api_key')
export UPDATE_INTERVAL=$(bashio::config 'update_interval')
export CURRENCY=$(bashio::config 'currency')
export ENABLE_CASHFLOW=$(bashio::config 'enable_cashflow_sensor')
export ENABLE_OUTFLOW=$(bashio::config 'enable_outflow_sensor')
export ENABLE_LIABILITY=$(bashio::config 'enable_liability_sensor')
export ENABLE_ACCOUNTS=$(bashio::config 'enable_account_sensors')
export ENABLE_TRANSACTIONS=$(bashio::config 'enable_transaction_sensors')
export CACHE_DURATION=$(bashio::config 'cache_duration')

# Get Home Assistant URL and token
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"
export HASS_URL="http://supervisor/core"

bashio::log.info "Starting Sure Finance addon..."
bashio::log.info "Update interval: ${UPDATE_INTERVAL} seconds"
bashio::log.info "Currency: ${CURRENCY}"

# Run the Python application
python3 /app/main.py