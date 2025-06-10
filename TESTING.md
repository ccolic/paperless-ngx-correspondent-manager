# Testing Documentation

This document describes the comprehensive test suite for the Paperless-ngx Correspondent Manager.

## Test Structure

The test suite is organized into several categories:

### Unit Tests (`test_manager.py`)
Tests for the core `PaperlessCorrespondentManager` class functionality:

- **Initialization Tests**: Verify proper setup of the manager class
- **API Communication Tests**: Test HTTP requests and error handling
- **Duplicate Detection Tests**: Verify exact and fuzzy duplicate finding
- **Similarity Calculation Tests**: Test the string similarity algorithms
- **Document Management Tests**: Test document retrieval and reassignment
- **Correspondent Management Tests**: Test CRUD operations on correspondents
- **Bulk Operations Tests**: Test batch processing and error recovery

### CLI Tests (`test_cli.py`)
Tests for the command-line interface:

- **Basic CLI Setup**: Environment variables, parameter validation
- **Command Tests**: All CLI commands (`list`, `find-duplicates`, `merge`, etc.)
- **Output Format Tests**: JSON, YAML, and table output formats
- **Error Handling Tests**: Invalid parameters, network errors
- **User Interaction Tests**: Confirmation prompts, input validation

### Integration Tests (`test_integration.py`)
End-to-end workflow tests:

- **Complete Workflows**: Full duplicate detection and merge processes
- **Complex Scenarios**: Multi-step operations, error recovery
- **Performance Tests**: Large datasets, batching behavior
- **API Compatibility Tests**: Version headers, URL handling

### Test Utilities (`test_utils.py`)
Helper functions and fixtures for testing:

- **Mock Builders**: Configurable mock objects for complex scenarios
- **Test Data Factories**: Consistent test data generation
- **Assertion Helpers**: Specialized assertions for CLI and API testing

## Test Coverage

The test suite covers:

### Core Manager Functionality
- ✅ Correspondent retrieval (paginated and single-page)
- ✅ Exact duplicate detection (case-insensitive, whitespace handling)
- ✅ Fuzzy similarity matching with configurable thresholds
- ✅ Document retrieval and filtering by correspondent
- ✅ Bulk document reassignment with batching
- ✅ Error handling and network resilience
- ✅ Empty correspondent detection and cleanup
- ✅ Correspondent diagnosis and detailed reporting

### CLI Interface
- ✅ All command-line commands and options
- ✅ Multiple output formats (table, JSON, YAML)
- ✅ Environment variable configuration
- ✅ User confirmation prompts
- ✅ Error messages and help text
- ✅ Parameter validation and edge cases

### Integration Scenarios
- ✅ Complete duplicate management workflows
- ✅ Large dataset handling and performance
- ✅ API pagination and error recovery
- ✅ Complex merge operations with user interaction
- ✅ Document restoration workflows

## Running Tests

### Quick Test Run
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_manager.py -v       # Unit tests
python -m pytest tests/test_cli.py -v          # CLI tests
python -m pytest tests/test_integration.py -v  # Integration tests
```

### Comprehensive Test Run with Coverage
```bash
# Run with coverage report
python -m pytest tests/ -v --cov=src/paperless_ngx_correspondent_manager --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=src/paperless_ngx_correspondent_manager --cov-report=html
```

### Test Runner Script
```bash
# Use the comprehensive test runner
python run_tests.py
```

## Test Fixtures and Mock Data

### Sample Data
The test suite includes comprehensive sample data:

- **5 Sample Correspondents**: Including duplicates, similar names, and empty correspondents
- **3 Sample Documents**: With various correspondent assignments
- **Paginated API Responses**: For testing pagination handling
- **Error Scenarios**: Network timeouts, API errors, invalid data

### Mock Configuration
Tests use sophisticated mocking to simulate:

- **API Responses**: Realistic paperless-ngx API responses
- **Network Conditions**: Timeouts, errors, slow responses
- **User Interactions**: Input prompts, confirmations
- **File System Operations**: For CLI testing

## Test Patterns and Best Practices

### AIDEV-NOTE Comments
Tests include `AIDEV-NOTE:` comments to explain:
- Complex mocking scenarios
- Performance-critical test paths
- Integration test boundaries
- Edge case handling strategies

### Mocking Strategy
- **Unit Tests**: Mock external dependencies (requests, user input)
- **Integration Tests**: Mock only the actual paperless-ngx API
- **CLI Tests**: Mock the manager class, test CLI logic in isolation

### Error Testing
- Network errors and timeouts
- Invalid API responses
- User cancellation scenarios
- Malformed input data

## Continuous Integration

The test suite is designed to run in CI environments:

- **No External Dependencies**: All API calls are mocked
- **Deterministic Results**: No random data or timing dependencies
- **Fast Execution**: Unit tests complete in seconds
- **Clear Reporting**: Detailed failure messages and coverage reports

## Test Data Management

### Fixtures in conftest.py
- `sample_correspondents`: Realistic correspondent data with edge cases
- `sample_documents`: Document data with various correspondent relationships
- `mock_session`: Pre-configured requests session mock
- `manager_instance`: Ready-to-use manager instance for testing

### Test Utilities
- `create_test_correspondent()`: Generate correspondent data for specific test scenarios
- `create_test_document()`: Generate document data with customizable fields
- `MockManagerBuilder`: Fluent API for building complex test scenarios

## Debugging Tests

### Running Individual Tests
```bash
# Run a specific test class
python -m pytest tests/test_manager.py::TestGetCorrespondents -v

# Run a specific test method
python -m pytest tests/test_manager.py::TestGetCorrespondents::test_get_correspondents_success_single_page -v
```

### Debugging with Print Statements
```bash
# Run with print output visible
python -m pytest tests/test_manager.py -v -s
```

### Coverage Analysis
```bash
# See which lines aren't covered
python -m pytest tests/ --cov=src/paperless_ngx_correspondent_manager --cov-report=term-missing --cov-fail-under=90
```

## Known Test Limitations

1. **Real API Testing**: Tests use mocks, not real paperless-ngx instances
2. **Performance Testing**: Limited load testing with simulated large datasets
3. **UI Testing**: No browser-based testing (CLI only)
4. **Version Compatibility**: Tests assume paperless-ngx API v9

## Contributing to Tests

When adding new functionality:

1. **Add Unit Tests**: Test the core logic in isolation
2. **Add CLI Tests**: Test the command-line interface
3. **Add Integration Tests**: Test end-to-end workflows
4. **Update Documentation**: Add test descriptions to this file
5. **Check Coverage**: Ensure new code has adequate test coverage

### Test File Naming
- `test_*.py`: Test files
- `Test*`: Test classes
- `test_*`: Test methods
- Follow the existing naming patterns for consistency
