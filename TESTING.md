# AirLatex.vim Testing Guide

This document describes how to run tests for the AirLatex.vim plugin.

## Test Structure

The test suite is organized as follows:

```
tests/
├── unit/                          # Unit tests
│   ├── lib/                       # Library module tests
│   │   ├── test_range.py         # FenwickTree and NaiveAccumulator tests
│   │   ├── test_uuid.py          # ID generation tests
│   │   ├── test_task.py          # Async task coordination tests
│   │   ├── test_connection.py    # Web utilities tests
│   │   └── test_settings.py      # Settings singleton tests
│   ├── buffers/                   # Buffer module tests
│   │   ├── controllers/
│   │   │   ├── test_text.py      # Text operations and diff tests
│   │   │   └── test_range.py     # Interval tree operations tests
│   │   └── test_document.py      # Document buffer tests
│   ├── test_session.py           # Session management tests
│   └── test_project.py           # Project and WebSocket tests
└── integration/                   # Integration tests (future)
```

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Install runtime dependencies:

```bash
pip install pynvim tornado requests beautifulsoup4 intervaltree
```

## Running Tests

### Quick Start

Use the provided test runner script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Manual Test Execution

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run tests with coverage report:

```bash
pytest --cov=rplugin/python3/airlatex --cov-report=term-missing
```

Run specific test file:

```bash
pytest tests/unit/lib/test_range.py
```

Run specific test class:

```bash
pytest tests/unit/lib/test_range.py::TestFenwickTree
```

Run specific test:

```bash
pytest tests/unit/lib/test_range.py::TestFenwickTree::test_initialization_empty
```

Run tests by marker:

```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
```

### Test Options

Common pytest options:

- `-v` or `--verbose`: Verbose output
- `-s`: Show print statements
- `-x`: Stop on first failure
- `--lf`: Run last failed tests
- `--ff`: Run failed tests first
- `-k EXPRESSION`: Run tests matching expression
- `--maxfail=N`: Stop after N failures

## Test Coverage

View coverage report in terminal:

```bash
pytest --cov=rplugin/python3/airlatex --cov-report=term-missing
```

Generate HTML coverage report:

```bash
pytest --cov=rplugin/python3/airlatex --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

## Test Modules

### Core Library Tests

**test_range.py** - Tests for FenwickTree and NaiveAccumulator
- Binary indexed tree operations
- Cumulative value calculations
- Search functionality
- Insert/remove operations
- Comparison between FenwickTree and NaiveAccumulator

**test_uuid.py** - Tests for ID generation utilities
- Unique ID generation
- Comment ID generation with increments
- Timestamp generation
- Format validation

**test_task.py** - Tests for async task coordination
- Task creation and chaining
- Async/await handling
- Vim callback integration
- Exception handling

**test_connection.py** - Tests for web utilities
- WebPage fetching and parsing
- BeautifulSoup integration
- Meta tag extraction
- Error handling

**test_settings.py** - Tests for settings singleton
- Singleton pattern implementation
- Configuration management
- URL construction

### Buffer Controller Tests

**test_text.py** - Tests for text operations
- Diff generation (buildOps)
- Operation application (applyOp)
- Insert/delete operations
- Multi-line edits
- Content hashing

**test_range.py** - Tests for interval tree operations
- Range tracking
- Overlapping intervals
- Comment thread management
- Tracked changes management
- Position calculations

### Session and Project Tests

**test_session.py** - Tests for session management
- Authentication
- Cookie handling
- Project list management
- WebSocket URL generation

**test_project.py** - Tests for project handling
- Message parsing
- Operational transforms
- WebSocket communication

**test_document.py** - Tests for document buffers
- Document structure
- Cursor tracking
- Highlighting

## Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestYourFeature:

    def test_basic_functionality(self):
        # Arrange
        obj = YourClass()

        # Act
        result = obj.method()

        # Assert
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        result = await async_function()
        assert result is not None
```

### Mocking

Use mocks for external dependencies:

```python
@patch('module.external_dependency')
def test_with_mock(self, mock_dependency):
    mock_dependency.return_value = "mocked value"
    # Test code
```

### Async Tests

Mark async tests with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await my_async_function()
    assert result is not None
```

## Continuous Integration

To run tests in CI/CD:

```bash
pytest --cov=rplugin/python3/airlatex --cov-report=xml
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running tests from the project root:

```bash
cd /workspace/AirLatex.vim/rascal
pytest
```

### Missing Dependencies

Install all dependencies:

```bash
pip install -r requirements-dev.txt
pip install pynvim tornado requests beautifulsoup4 intervaltree
```

### Async Test Failures

Make sure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

## Test Metrics

Current test coverage by module:

- `lib/range.py` - FenwickTree and NaiveAccumulator: Comprehensive
- `lib/uuid.py` - ID generation: Comprehensive
- `lib/task.py` - Async coordination: Comprehensive
- `lib/connection.py` - Web utilities: Comprehensive
- `lib/settings.py` - Settings: Comprehensive
- `buffers/controllers/text.py` - Text operations: Comprehensive
- `buffers/controllers/range.py` - Range operations: Comprehensive
- `session.py` - Session management: Good
- `project.py` - Basic coverage
- `buffers/document.py` - Basic coverage

## Future Improvements

- Add integration tests for full workflows
- Add performance benchmarks for FenwickTree
- Add end-to-end tests with mock Overleaf server
- Increase coverage for project.py and document.py
- Add property-based testing for operational transforms
