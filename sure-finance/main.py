#!/usr/bin/env python3
"""Main entry point for Sure Finance Home Assistant addon.

This script runs the web interface and manages the integration
with Home Assistant.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

import coloredlogs
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.api_client import SureFinanceClient
from src.cache_manager import CacheManager
from src.data_manager import DataManager
from src.financial_calculator import FinancialCalculator

# Configure logging
coloredlogs.install(
    level='INFO',
    fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sure Finance Home Assistant Addon",
    description="Financial tracking addon for Home Assistant",
    version="1.0.2"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
api_client = None
cache_manager = None
data_manager = None
calculator = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global api_client, cache_manager, data_manager, calculator
    
    # Get configuration from environment
    api_key = os.environ.get("API_KEY")
    if not api_key:
        logger.error("API_KEY not configured")
        sys.exit(1)
    
    update_interval = int(os.environ.get("UPDATE_INTERVAL", "300"))
    currency = os.environ.get("CURRENCY", "USD")
    cache_duration = int(os.environ.get("CACHE_DURATION", "3600"))
    base_url = os.environ.get("HOST") or os.environ.get("BASE_URL") or os.environ.get("SURE_API_BASE_URL")

    # Initialize components
    logger.info("Initializing Sure Finance addon...")
    
    # API client
    api_client = SureFinanceClient(api_key=api_key, base_url=base_url)
    await api_client.connect()
    
    # Cache manager
    cache_manager = CacheManager(
        cache_dir=Path("/data/cache"),
        default_ttl=cache_duration
    )
    await cache_manager.connect_redis()
    
    # Financial calculator
    calculator = FinancialCalculator(currency=currency)
    
    # Data manager
    data_manager = DataManager(
        api_client=api_client,
        cache_manager=cache_manager,
        calculator=calculator,
        update_interval=update_interval
    )
    
    # Start periodic sync
    asyncio.create_task(data_manager.periodic_sync())
    
    # Initial data sync
    try:
        await data_manager.sync_all_data()
        logger.info("Initial data sync completed")
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")
    
    logger.info("Sure Finance addon started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    if api_client:
        await api_client.close()
    if cache_manager:
        await cache_manager.close()
    logger.info("Sure Finance addon stopped")


@app.get("/")
async def root():
    """Serve the web interface."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Sure Finance - Home Assistant Addon</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .metric-card {
            text-align: center;
            padding: 1.5rem;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .positive { color: #48c774; }
        .negative { color: #f14668; }
    </style>
</head>
<body>
    <section class="hero is-primary">
        <div class="hero-body">
            <div class="container">
                <h1 class="title">Sure Finance</h1>
                <h2 class="subtitle">Financial Dashboard</h2>
            </div>
        </div>
    </section>
    
    <section class="section">
        <div class="container">
            <div class="columns is-multiline">
                <div class="column is-3">
                    <div class="card metric-card">
                        <div class="card-content">
                            <p class="title is-5">Net Worth</p>
                            <p class="metric-value" id="net-worth">Loading...</p>
                        </div>
                    </div>
                </div>
                <div class="column is-3">
                    <div class="card metric-card">
                        <div class="card-content">
                            <p class="title is-5">Monthly Income</p>
                            <p class="metric-value positive" id="income">Loading...</p>
                        </div>
                    </div>
                </div>
                <div class="column is-3">
                    <div class="card metric-card">
                        <div class="card-content">
                            <p class="title is-5">Monthly Expenses</p>
                            <p class="metric-value negative" id="expenses">Loading...</p>
                        </div>
                    </div>
                </div>
                <div class="column is-3">
                    <div class="card metric-card">
                        <div class="card-content">
                            <p class="title is-5">Total Liabilities</p>
                            <p class="metric-value negative" id="liabilities">Loading...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="columns">
                <div class="column is-6">
                    <div class="card">
                        <div class="card-content">
                            <p class="title is-5">Cashflow Trend</p>
                            <div id="cashflow-chart"></div>
                        </div>
                    </div>
                </div>
                <div class="column is-6">
                    <div class="card">
                        <div class="card-content">
                            <p class="title is-5">Expense Breakdown</p>
                            <div id="expense-chart"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="columns">
                <div class="column">
                    <div class="card">
                        <div class="card-content">
                            <p class="title is-5">Account Balances</p>
                            <table class="table is-fullwidth" id="accounts-table">
                                <thead>
                                    <tr>
                                        <th>Account</th>
                                        <th>Type</th>
                                        <th>Balance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td colspan="3">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <script>
        function formatCurrency(amount, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        }
        
        async function loadDashboard() {
            try {
                // Load summary
                const summaryRes = await fetch('api/summary');
                const summary = await summaryRes.json();
                
                document.getElementById('net-worth').textContent = 
                    formatCurrency(summary.net_worth, summary.currency);
                document.getElementById('liabilities').textContent = 
                    formatCurrency(summary.total_liabilities, summary.currency);
                
                // Load monthly data
                const monthlyRes = await fetch('api/monthly');
                const monthly = await monthlyRes.json();
                
                document.getElementById('income').textContent = 
                    formatCurrency(monthly.total_income, monthly.currency);
                document.getElementById('expenses').textContent = 
                    formatCurrency(monthly.total_expenses, monthly.currency);
                
                // Update expense breakdown chart
                const expenseData = [{
                    values: Object.values(monthly.expenses_by_category),
                    labels: Object.keys(monthly.expenses_by_category),
                    type: 'pie'
                }];
                
                Plotly.newPlot('expense-chart', expenseData, {
                    height: 300,
                    margin: {t: 0, b: 0}
                });
                
                // Load accounts
                const accountsRes = await fetch('api/accounts');
                const accounts = await accountsRes.json();
                
                const tbody = document.querySelector('#accounts-table tbody');
                tbody.innerHTML = accounts.map(acc => `
                    <tr>
                        <td>${acc.account_name}</td>
                        <td>${acc.classification}</td>
                        <td class="${acc.balance >= 0 ? 'positive' : 'negative'}">
                            ${formatCurrency(acc.balance, acc.currency)}
                        </td>
                    </tr>
                `).join('');
                
                // Load trends
                const trendsRes = await fetch('api/trends');
                const trends = await trendsRes.json();
                
                const cashflowData = [
                    {
                        x: Object.keys(trends),
                        y: Object.values(trends).map(t => t.total_income),
                        name: 'Income',
                        type: 'scatter',
                        line: {color: '#48c774'}
                    },
                    {
                        x: Object.keys(trends),
                        y: Object.values(trends).map(t => t.total_expenses),
                        name: 'Expenses',
                        type: 'scatter',
                        line: {color: '#f14668'}
                    }
                ];
                
                Plotly.newPlot('cashflow-chart', cashflowData, {
                    height: 300,
                    margin: {t: 0},
                    xaxis: {title: 'Month'},
                    yaxis: {title: 'Amount'}
                });
                
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }
        
        // Load dashboard on page load
        loadDashboard();
        
        // Refresh every 5 minutes
        setInterval(loadDashboard, 300000);
    </script>
</body>
</html>
    """)


@app.get("/api/summary")
async def get_summary():
    """Get financial summary."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        summary = await data_manager.get_financial_summary()
        return summary.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monthly")
async def get_monthly():
    """Get current month cashflow."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        from datetime import datetime
        now = datetime.utcnow()
        monthly = await data_manager.get_monthly_cashflow(now.year, now.month)
        return monthly.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Error getting monthly data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts")
async def get_accounts():
    """Get account balances."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        accounts = await data_manager.get_accounts()
        balances = calculator.get_account_balances(accounts)
        return [b.model_dump(mode="json") for b in balances]
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends")
async def get_trends():
    """Get monthly trends."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        transactions = await data_manager.get_transactions(days=365)
        trends = calculator.calculate_monthly_trends(transactions, months=12)
        return {k: v.model_dump(mode="json") for k, v in trends.items()}
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh")
async def refresh_data():
    """Manually refresh all data."""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        await data_manager.sync_all_data()
        return {"status": "success", "message": "Data refreshed"}
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the web server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8099,
        log_level="info",
        access_log=True
    )