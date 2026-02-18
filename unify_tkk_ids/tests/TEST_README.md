# Testing Guide for unify_tkk_ids

This directory contains comprehensive tests for the `unify_tkk_ids.py` script that unifies TKK Group IDs in JSON textcritic files and corresponding SVG files.

## Setup

1. Install testing dependencies:
```bash
pip install -r test-requirements.txt
```

2. Ensure you have Python 3.7+ installed.

## Running Tests

### Quick Start
```bash
# Run all tests
python -m pytest test_unify_tkk_ids.py

# Or use the test runner
python run_tests.py
```

### Test Categories

#### Unit Tests
Test individual functions in isolation:
```bash
python run_tests.py -unit
```

#### Integration Tests  
Test the complete workflow with temporary files:
```bash
python run_tests.py -int
```

#### With Coverage
Generate a coverage report:
```bash
python run_tests.py -cov
```

## Test Structure

### `TestExtractNumbers`
Tests the `extract_numbers()` function that extracts digits from text strings:
- Simple number extraction
- Multiple numbers in one string  
- Edge cases (no numbers, only numbers, None input)

### `TestDisplayUncertainties`
Tests the `display_uncertainties()` function that validates ID updates:
- No errors (all IDs properly updated)
- JSON errors (unchanged IDs in JSON)
- SVG orphans (unchanged IDs in SVG files)
- TODO entries are properly ignored

### `TestGetRelevantSvgs`
Tests the `get_relevant_svgs()` function that finds matching SVG files:
- Standard entries (non-SkRT)
- SkRT entries (Reihentabelle files)
- No matches found
- Empty file lists

### `TestUpdateSvgId`
Tests the `update_svg_id()` function that updates IDs in SVG content:
- Different attribute orders (class before id, id before class)
- Single vs double quotes
- Only updates elements with `class="tkk"`
- Multiple occurrences

### `TestProcessTkkIds`
Integration tests for the main `process_tkk_ids()` function:
- Successful processing workflow
- Error handling (missing files/directories)
- File I/O operations

### `TestIntegration`
Full integration tests with temporary files:
- Complete workflow from JSON to SVG updates
- File structure validation
- Data loading and processing

### `TestEdgeCases`
Edge cases and error conditions:
- Special characters in text
- Malformed JSON structures
- Empty data sets

## Test Data

The tests automatically create temporary test data including:

- **JSON files**: Sample textcritics.json with various ID patterns
- **SVG files**: Sample SVG files with different class and id configurations
- **Directory structure**: Temporary directories that mirror real usage

## Coverage

Run with coverage to see which parts of the code are tested:
```bash
pytest --cov=unify_tkk_ids --cov-report=html
```

This generates an HTML coverage report in the `htmlcov/` directory.

## Continuous Integration

The test suite is designed to:
- Run in isolated environments
- Clean up temporary files automatically
- Provide clear error messages
- Support parallel execution

## Adding New Tests

When adding new functionality:

1. Create unit tests for individual functions
2. Add integration tests for workflows  
3. Include edge cases and error conditions
4. Update this README with new test descriptions

## Example Test Run Output

```
$ python run_tests.py -cov

======== test session starts ========
collected 25 items

test_unify_tkk_ids.py::TestExtractNumbers::test_extract_numbers_simple PASSED
test_unify_tkk_ids.py::TestExtractNumbers::test_extract_numbers_multiple PASSED
...
test_unify_tkk_ids.py::TestProcessTkkIds::test_process_tkk_ids_success PASSED

======== 25 passed in 2.34s ========

Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
unify_tkk_ids.py       145     12    92%   23-25, 187-190
--------------------------------------------------
TOTAL                  145     12    92%
```