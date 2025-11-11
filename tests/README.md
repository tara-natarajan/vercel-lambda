# Canvas Webhook Handler Tests

## Overview

This directory contains unit tests for the Canvas webhook handler. The tests mock the Benchling API to allow testing the business logic without making actual API calls.

## Running Tests

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=api --cov-report=term-missing
```

### Run Tests in Verbose Mode

```bash
pytest tests/ -v
```

### Run a Specific Test File

```bash
pytest tests/test_canvas.py -v
```

### Run a Specific Test Class

```bash
pytest tests/test_canvas.py::TestGetInitialCanvasBlocks -v
```

### Run a Specific Test

```bash
pytest tests/test_canvas.py::TestGetInitialCanvasBlocks::test_displays_number_of_plates -v
```

## Test Structure

### `test_canvas.py`

Contains all unit tests for the canvas webhook handler:

#### `TestGetInitialCanvasBlocks`
- Tests the `get_initial_canvas_blocks()` function
- Verifies UI block structure
- Validates Number of Plates display
- Checks default values

#### `TestCanvasHandler`
- Tests webhook handler methods
- Validates data extraction from payloads
- Tests environment variable checks
- Mocks Benchling API calls

#### `TestPayloadParsing`
- Tests parsing of different webhook payload formats
- Validates support for new app signals format
- Tests fallback to old format

#### `TestUpdateCanvas`
- Tests the `update_canvas()` function
- Mocks Benchling client
- Validates API call parameters

## Continuous Integration

Tests automatically run on every push and pull request via GitHub Actions.

See `.github/workflows/test.yml` for the CI configuration.

## Writing New Tests

When adding new functionality:

1. Add corresponding tests to `test_canvas.py`
2. Use `@patch` decorators to mock external dependencies
3. Test both success and error paths
4. Ensure tests are isolated (no dependencies on external APIs)

### Example Test

```python
@patch('api.canvas.get_benchling_client')
def test_new_feature(self, mock_get_client):
    """Test description."""
    # Setup
    mock_client = Mock()
    mock_get_client.return_value = mock_client
    
    # Execute
    result = your_function()
    
    # Assert
    assert result == expected_value
    assert mock_client.method.called
```

## Mocking Strategy

The tests use Python's `unittest.mock` to:

1. **Mock Benchling Client**: Prevents actual API calls
2. **Mock Environment Variables**: Tests different configurations
3. **Mock HTTP Handler**: Tests request/response handling

This allows us to:
- Test logic without external dependencies
- Run tests quickly
- Test error conditions safely
- Validate behavior in isolation

