# Contributing to Sure Finance Home Assistant Addon

Thank you for your interest in contributing to the Sure Finance Home Assistant addon! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## How to Contribute

### Reporting Issues

1. **Check existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Home Assistant version
   - Addon version
   - Error logs
   - Steps to reproduce

### Suggesting Features

1. **Open a discussion** first to gauge interest
2. **Provide use cases** and examples
3. **Consider implementation complexity**
4. **Be patient** - features take time to implement

### Submitting Code

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/juanmaus/sure-finance-hass-addon.git
cd sure-finance-hass-addon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r sure-finance/requirements.txt
pip install -r sure-finance/requirements-dev.txt
```

#### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Follow the coding style guide
   - Add tests for new functionality
   - Update documentation

4. **Run tests**:
   ```bash
   cd sure-finance
   python -m pytest tests/ -v
   ```

5. **Run linting**:
   ```bash
   flake8 src/
   black src/ tests/
   mypy src/
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### Code Organization

```python
# Good
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp
from pydantic import BaseModel

from .models import Account


class FinancialService:
    """Service for financial calculations."""
    
    def __init__(self, currency: str = "USD"):
        """Initialize service.
        
        Args:
            currency: Default currency code
        """
        self.currency = currency
    
    async def calculate_net_worth(
        self,
        accounts: List[Account]
    ) -> Decimal:
        """Calculate total net worth.
        
        Args:
            accounts: List of accounts
            
        Returns:
            Net worth amount
        """
        # Implementation
```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Examples:
```
feat: add support for multiple currencies
fix: correct calculation of monthly savings rate
docs: update API reference for new endpoints
```

## Testing

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock

from src.financial_calculator import FinancialCalculator


class TestFinancialCalculator:
    """Test financial calculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return FinancialCalculator()
    
    def test_calculate_savings_rate(self, calculator):
        """Test savings rate calculation."""
        rate = calculator.calculate_savings_rate(
            income=Decimal("5000"),
            expenses=Decimal("3000")
        )
        assert rate == Decimal("40")
    
    @pytest.mark.asyncio
    async def test_async_operation(self, calculator):
        """Test async operation."""
        # Test implementation
```

### Test Coverage

- Aim for >80% code coverage
- Test edge cases and error conditions
- Include integration tests

## Documentation

### Docstring Format

Use Google style docstrings:

```python
def calculate_cashflow(
    transactions: List[Transaction],
    start_date: datetime,
    end_date: datetime
) -> CashflowSummary:
    """Calculate cashflow for a period.
    
    Args:
        transactions: List of transactions to analyze
        start_date: Period start date
        end_date: Period end date
        
    Returns:
        Cashflow summary with income and expenses
        
    Raises:
        ValueError: If date range is invalid
    """
```

### Updating Documentation

1. Update relevant `.md` files
2. Update inline code comments
3. Update configuration examples
4. Add migration notes if needed

## Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation**
3. **Add entry to CHANGELOG.md**
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] Code follows style guide
- [ ] All tests pass
- [ ] No linting errors

## Release Process

1. Update version in:
   - `config.json`
   - `src/manifest.json`
   - `src/__init__.py`
   
2. Update CHANGELOG.md

3. Create release tag:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

## Getting Help

- **Discord**: [Join our server](https://discord.gg/example)
- **Discussions**: Use GitHub Discussions
- **Email**: maintainer@example.com

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing!