/**
 * Sure Finance Lovelace Cards
 * Custom cards for displaying financial data in Home Assistant
 */

class SureFinanceSummaryCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    
    if (!this.content) {
      const card = document.createElement('ha-card');
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    }
    
    this._updateCard();
  }
  
  setConfig(config) {
    if (!config.entities) {
      throw new Error('You need to define entities');
    }
    this.config = config;
  }
  
  _updateCard() {
    const netWorthEntity = this._hass.states[this.config.entities.net_worth];
    const cashflowEntity = this._hass.states[this.config.entities.cashflow];
    const outflowEntity = this._hass.states[this.config.entities.outflow];
    const liabilityEntity = this._hass.states[this.config.entities.liability];
    const savingsRateEntity = this._hass.states[this.config.entities.savings_rate];
    
    const formatCurrency = (value, unit) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: unit || 'USD'
      }).format(value);
    };
    
    this.content.innerHTML = `
      <style>
        .sure-finance-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
        }
        .metric {
          text-align: center;
        }
        .metric-value {
          font-size: 24px;
          font-weight: bold;
          margin: 8px 0;
        }
        .metric-label {
          color: var(--secondary-text-color);
          font-size: 14px;
        }
        .positive { color: var(--success-color, #4caf50); }
        .negative { color: var(--error-color, #f44336); }
        .neutral { color: var(--primary-text-color); }
      </style>
      
      <div class="sure-finance-summary">
        <div class="metric">
          <div class="metric-label">Net Worth</div>
          <div class="metric-value ${netWorthEntity?.state >= 0 ? 'positive' : 'negative'}">
            ${netWorthEntity ? formatCurrency(netWorthEntity.state, netWorthEntity.attributes.unit_of_measurement) : 'N/A'}
          </div>
        </div>
        
        <div class="metric">
          <div class="metric-label">Monthly Income</div>
          <div class="metric-value positive">
            ${cashflowEntity ? formatCurrency(cashflowEntity.attributes.monthly_income, cashflowEntity.attributes.unit_of_measurement) : 'N/A'}
          </div>
        </div>
        
        <div class="metric">
          <div class="metric-label">Monthly Expenses</div>
          <div class="metric-value negative">
            ${outflowEntity ? formatCurrency(outflowEntity.attributes.monthly_expenses, outflowEntity.attributes.unit_of_measurement) : 'N/A'}
          </div>
        </div>
        
        <div class="metric">
          <div class="metric-label">Total Liabilities</div>
          <div class="metric-value negative">
            ${liabilityEntity ? formatCurrency(liabilityEntity.state, liabilityEntity.attributes.unit_of_measurement) : 'N/A'}
          </div>
        </div>
        
        <div class="metric">
          <div class="metric-label">Savings Rate</div>
          <div class="metric-value neutral">
            ${savingsRateEntity ? savingsRateEntity.state + '%' : 'N/A'}
          </div>
        </div>
      </div>
    `;
  }
  
  static getConfigElement() {
    return document.createElement('sure-finance-summary-card-editor');
  }
  
  static getStubConfig() {
    return {
      entities: {
        net_worth: 'sensor.sure_finance_net_worth',
        cashflow: 'sensor.sure_finance_total_cashflow',
        outflow: 'sensor.sure_finance_total_outflow',
        liability: 'sensor.sure_finance_total_liability',
        savings_rate: 'sensor.sure_finance_monthly_savings_rate'
      }
    };
  }
}

class SureFinanceExpenseCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = this.config?.title || 'Expense Breakdown';
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    }
    
    this._updateCard();
  }
  
  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
  }
  
  _updateCard() {
    const entity = this._hass.states[this.config.entity];
    
    if (!entity || !entity.attributes.expenses_by_category) {
      this.content.innerHTML = '<p>No expense data available</p>';
      return;
    }
    
    const expenses = entity.attributes.expenses_by_category;
    const total = Object.values(expenses).reduce((sum, val) => sum + val, 0);
    
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: entity.attributes.unit_of_measurement || 'USD'
      }).format(value);
    };
    
    const sortedExpenses = Object.entries(expenses)
      .sort(([,a], [,b]) => b - a)
      .slice(0, this.config.max_items || 10);
    
    this.content.innerHTML = `
      <style>
        .expense-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .expense-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .expense-bar {
          flex: 1;
          margin: 0 12px;
          height: 20px;
          background: var(--divider-color);
          border-radius: 4px;
          overflow: hidden;
          position: relative;
        }
        .expense-fill {
          height: 100%;
          background: var(--primary-color);
          transition: width 0.3s ease;
        }
        .expense-category {
          min-width: 120px;
          font-size: 14px;
        }
        .expense-amount {
          min-width: 80px;
          text-align: right;
          font-size: 14px;
          font-weight: 500;
        }
      </style>
      
      <div class="expense-list">
        ${sortedExpenses.map(([category, amount]) => `
          <div class="expense-item">
            <span class="expense-category">${category}</span>
            <div class="expense-bar">
              <div class="expense-fill" style="width: ${(amount / total) * 100}%"></div>
            </div>
            <span class="expense-amount">${formatCurrency(amount)}</span>
          </div>
        `).join('')}
      </div>
      
      <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--divider-color); text-align: center;">
        <strong>Total: ${formatCurrency(total)}</strong>
      </div>
    `;
  }
  
  static getConfigElement() {
    return document.createElement('sure-finance-expense-card-editor');
  }
  
  static getStubConfig() {
    return {
      entity: 'sensor.sure_finance_total_outflow',
      title: 'Monthly Expenses',
      max_items: 10
    };
  }
}

class SureFinanceAccountsCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = this.config?.title || 'Account Balances';
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    }
    
    this._updateCard();
  }
  
  setConfig(config) {
    if (!config.entities || !Array.isArray(config.entities)) {
      throw new Error('You need to define entities as an array');
    }
    this.config = config;
  }
  
  _updateCard() {
    const formatCurrency = (value, unit) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: unit || 'USD'
      }).format(value);
    };
    
    const accounts = this.config.entities
      .map(entityId => this._hass.states[entityId])
      .filter(entity => entity);
    
    if (accounts.length === 0) {
      this.content.innerHTML = '<p>No account data available</p>';
      return;
    }
    
    this.content.innerHTML = `
      <style>
        .accounts-table {
          width: 100%;
          border-collapse: collapse;
        }
        .accounts-table th,
        .accounts-table td {
          padding: 8px;
          text-align: left;
        }
        .accounts-table th {
          font-weight: 500;
          color: var(--secondary-text-color);
          font-size: 12px;
          text-transform: uppercase;
        }
        .accounts-table tr:not(:last-child) td {
          border-bottom: 1px solid var(--divider-color);
        }
        .balance {
          text-align: right;
          font-weight: 500;
        }
        .positive { color: var(--success-color, #4caf50); }
        .negative { color: var(--error-color, #f44336); }
      </style>
      
      <table class="accounts-table">
        <thead>
          <tr>
            <th>Account</th>
            <th>Type</th>
            <th style="text-align: right;">Balance</th>
          </tr>
        </thead>
        <tbody>
          ${accounts.map(entity => `
            <tr>
              <td>${entity.attributes.account_name || entity.attributes.friendly_name}</td>
              <td>${entity.attributes.classification || 'N/A'}</td>
              <td class="balance ${entity.state >= 0 ? 'positive' : 'negative'}">
                ${formatCurrency(entity.state, entity.attributes.unit_of_measurement)}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
  
  static getConfigElement() {
    return document.createElement('sure-finance-accounts-card-editor');
  }
  
  static getStubConfig() {
    return {
      title: 'Account Balances',
      entities: []
    };
  }
}

// Register the cards
customElements.define('sure-finance-summary-card', SureFinanceSummaryCard);
customElements.define('sure-finance-expense-card', SureFinanceExpenseCard);
customElements.define('sure-finance-accounts-card', SureFinanceAccountsCard);

// Register with Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'sure-finance-summary-card',
  name: 'Sure Finance Summary',
  description: 'Display financial summary from Sure Finance'
});
window.customCards.push({
  type: 'sure-finance-expense-card',
  name: 'Sure Finance Expenses',
  description: 'Display expense breakdown from Sure Finance'
});
window.customCards.push({
  type: 'sure-finance-accounts-card',
  name: 'Sure Finance Accounts',
  description: 'Display account balances from Sure Finance'
});