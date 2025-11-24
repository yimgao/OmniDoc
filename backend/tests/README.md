# Testing Guide

This directory contains the test suite for OmniDoc.

## Running Tests

### Prerequisites
```bash
# Install test dependencies
uv sync --all-extras
# or
pip install -e ".[dev]"
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
# From backend directory
cd backend
pytest --cov=src --cov-report=html

# Or from project root
pytest --cov=backend/src --cov-report=html
```

### Run Specific Test File
```bash
# From backend directory
cd backend
pytest tests/test_api.py
pytest tests/test_utils.py

# Or from project root
pytest backend/tests/test_api.py
pytest backend/tests/test_utils.py
```

### Run with Verbose Output
```bash
pytest -v
```

## Test Structure

- `test_api.py` - API endpoint tests
- `test_utils.py` - Utility function tests
- `test_backward_compatibility.py` - Backward compatibility tests
- `test_monitoring.py` - Monitoring and metrics tests
- `test_health.py` - Health check endpoint tests
- `test_websocket.py` - WebSocket functionality tests
- `conftest.py` - Pytest configuration and fixtures

## Test Categories

### Unit Tests
- Test individual functions and classes in isolation
- Fast execution
- No external dependencies

### Integration Tests
- Test API endpoints with test client
- May require database/Redis (marked with `@pytest.mark.skip`)
- Test full request/response cycle

### Backward Compatibility Tests
- Ensure API changes don't break existing clients
- Verify response structure compatibility
- Check format validation

## Writing New Tests

### Example Test
```python
def test_example():
    """Test description"""
    # Arrange
    value = "test"
    
    # Act
    result = function_to_test(value)
    
    # Assert
    assert result == expected_value
```

### Test Fixtures
Use fixtures from `conftest.py`:
```python
def test_with_client(test_client):
    response = test_client.get("/api/endpoint")
    assert response.status_code == 200
```

## Test Coverage Goals

- **Unit Tests**: >80% coverage for utility functions
- **Integration Tests**: All API endpoints covered
- **Error Cases**: Test error handling and edge cases
- **Validation**: Test input validation and sanitization

## Continuous Integration

Tests should pass before:
- Merging pull requests
- Deploying to production
- Creating releases

## Notes

- Some tests require running services (database, Redis) and are marked with `@pytest.mark.skip`
- Run full integration tests in CI/CD pipeline
- Mock external services when possible for faster tests

