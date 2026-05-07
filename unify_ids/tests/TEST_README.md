# Testing Guide for unify_ids

This directory contains comprehensive tests for the `unify_tkk_ids.py`, `unify_link_box_ids.py`, and `unify_kv_ids.py` scripts and their shared utility modules.

## Project Structure

The project now uses a clean package structure:
```
unify_ids/
├── unify_tkk_ids.py          # Main script
├── unify_link_box_ids.py     # Link-box unification script
├── unify_kv_ids.py           # KV ID unification script
├── utils/                    # Utility package
│   ├── __init__.py
│   ├── models.py             # Data models (dataclasses)
│   ├── constants.py          # Shared constants
│   ├── extraction_utils.py   # Data extraction functions
│   ├── file_utils.py         # File I/O operations
│   ├── logger_utils.py       # Processing logging
│   ├── svg_utils.py          # SVG processing functions
│   └── validation_utils.py   # Validation and reporting
├── tests/
│   ├── data/scenarios/       # Minimal JSON scenario fixtures for integration tests
│   ├── img/scenarios/        # Minimal SVG scenario fixtures for integration tests
│   ├── test_fixtures.py      # Shared test data and fixtures
│   ├── test_unify_kv_ids.py    # KV ID unification tests
│   ├── test_unify_tkk_ids.py  # Main script tests
│   ├── test_unify_link_box_ids.py
│   ├── test_unifier_main_contracts.py
│   ├── test_unifiers_integration.py
│   ├── test_extraction_utils.py
│   ├── test_file_utils.py
│   ├── test_logger_utils.py
│   ├── test_svg_utils.py
│   └── test_validation_utils.py
├── requirements-notebook.txt # Notebook-specific dependencies
├── requirements.txt          # All dependencies (including test deps)
└── pytest.ini
```

## Setup

See the [Virtual Environments](../../README.md#virtual-environments) section in the repo-level README for how to create and activate a virtual environment.

Once the virtual environment is active, install dependencies:

```bash
pip install -r requirements.txt --require-hashes
```

## Running Tests

### Quick Start
```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_validation_utils.py -v
```

## Coverage

Run with coverage to see which parts of the code are tested:
```bash
# Default run (coverage is configured in pytest.ini addopts)
pytest tests/

# Explicit full-coverage run (equivalent to default)
pytest tests/ --cov=utils --cov=unify_link_box_ids --cov=unify_tkk_ids --cov=unify_kv_ids --cov-report=html --cov-report=term

# Generate coverage for integration scenarios only (uses default coverage flags from pytest.ini)
pytest tests/ -m integration

# Coverage for specific module
pytest tests/test_validation_utils.py --cov=utils.validation_utils --cov-report=term
```

Coverage reports are generated in the `htmlcov/` directory and show line-by-line coverage for `unify_tkk_ids.py`, `unify_link_box_ids.py`, and all utility modules.

### Test Categories

#### Unit Tests
Test individual functions in isolation by module:
```bash
# Test extraction utilities
pytest tests/test_extraction_utils.py -v

# Test file operations
pytest tests/test_file_utils.py -v

# Test logger handling
pytest tests/test_logger_utils.py -v

# Test SVG processing
pytest tests/test_svg_utils.py -v

# Test validation functions
pytest tests/test_validation_utils.py -v
```

#### Integration Tests  
Test the complete workflow:
```bash
# Integration tests for all unifiers
pytest tests/test_unifiers_integration.py -v
```


## Test Structure

### Shared Test Fixtures (`test_fixtures.py`)
Centralized test data and helper functions used across all test modules:
- **JSON data structures**: Various prefixed/unprefixed ID configurations
- **SVG content samples**: Single/multiple files with different ID patterns
- **Organized sections**: Individual samples, JSON structures, SVG content

### Extraction Utils Tests (`test_extraction_utils.py`)
Tests for `utils/extraction_utils.py`:
- **`extract_file_info_list()`**: File info pre-computation (filename, MNR number, rowtable flag) from a list of SVG filenames
- **`extract_id_suffix()`**: Suffix letter derivation from `NvonM` filename patterns
- **`extract_link_boxes()`**: linkBox extraction from entry structures
- **`extract_moldenhauer_number()`**: Catalog number extraction from various ID formats
- **`extract_svg_group_ids()`**: svgGroupId collection from JSON comment structures
- **`has_class_token()`**: CSS class token presence checks
- Edge cases and different entry formats

### File Utils Tests (`test_file_utils.py`) 
Tests for `utils/file_utils.py`:
- **`load_json_file()`**: JSON file loading and error handling
- **`load_and_validate_inputs()`**: Composition of JSON and SVG loading with validation
- **`create_svg_loader()`**: SVG file caching system
- **`save_json_file()`**: JSON file writing with consistent formatting
- **`save_results()`**: Combined SVG and JSON save operation
- Error handling for missing files and permissions

### Logger Utils Tests (`test_logger_utils.py`)
Tests for `utils/logger_utils.py`:
- **`Logger` initialization**: Verify all stats counters initialize to 0
- **`log()` method**: Message formatting, list appending, and conditional printing
- **`print_report()` method**: Categorized output for errors, warnings, and info messages
- **`bump_stats()` method**: Counter increments and invalid-key error handling
- **`print_stats_summary()` method**: Formatted stats summary output

### SVG Utils Tests (`test_svg_utils.py`)
Tests for `utils/svg_utils.py`:
- **`build_id_to_file_index_by_class()`**: Builds an ID-to-file index for elements matching a target CSS class
- **`find_relevant_svg_files()`**: File filtering by entry type (TF, Sk, SkRT)
- **`update_svg_id_by_class()`**: ID replacement in SVG content with CSS class targeting
- Partial class name non-matches, multiple occurrences, invalid XML, and XML declaration handling

### Main Contract Tests (`test_unifier_main_contracts.py`)
Contract tests for script entry points:
- CLI and main-function behavior consistency
- Common execution contracts across unifier scripts

### Unifiers Integration Tests (`test_unifiers_integration.py`)
Integration tests for both unifier scripts:
- Scenario-based integration checks using minimal fixtures in `tests/data/scenarios` and `tests/img/scenarios`
- TKK scenarios: sketch-default single success, multi-ID single-file success, multi-file success, mixed Sk/SkRT success routing, Mx high-number success, missing SVG ID, dry-run persistence check, idempotency, TODO+mixed handling, SkRT rowtable-only behavior, and no-svgGroupIds no-op reporting; plus one dedicated Textfassung edge-case scenario
- Link-box scenarios: single success, multi-match JSON expansion, and missing `sheetId` no-op behavior
- Combined scenario: shared fixture with both TKK + link-box IDs updated in one sequential integration flow
- Input-path guard checks: missing JSON and missing SVG directory

### KV Script Tests (`test_unify_kv_ids.py`)
Unit and integration tests for `unify_kv_ids.py`:
- **`process_kv_ids_per_correction()`**: Sequential svgGroupId assignment across blockComments including idempotency, dry-run, mutation contract, and stats
- **`process_correction_entry()`**: Single correction entry processing and delegation to sub-functions
- **`unify_kv_ids()`**: Complete KV ID unification workflow including JSON read/write, dry-run, and idempotency
- **`main()`**: CLI entry point behavior and error handling

### Link Box Script Tests (`test_unify_link_box_ids.py`)
Unit tests for `unify_link_box_ids.py`:
- **`process_single_link_box()`**: Single link-box processing including SVG and JSON update
- **`process_textcritics_entry()`**: Entry-level link-box processing and iteration
- **`unify_link_box_ids()`**: Complete link-box unification workflow
- **`main()`**: CLI entry point behavior and error handling

### Tkk Script Tests (`test_unify_tkk_ids.py`)
Unit tests for `unify_tkk_ids.py`:
- **`process_single_svg_group_id()`**: Single ID processing workflow
- **`process_textcritics_entry()`**: Entry-level processing and counter management
- **`unify_tkk_ids()`**: Complete unification workflow including dry-run and idempotency
- **`main()`**: CLI entry point behavior and error handling

### Validation Utils Tests (`test_validation_utils.py`)
Tests for `utils/validation_utils.py`:
- **`display_validation_report()`**: Comprehensive validation reporting across success, orphan, TODO, empty, and malformed scenarios
- **`validate_json_entries()`**: JSON ID validation with TODO handling
- **`validate_svg_entries()`**: SVG orphan detection

## Test Data & Fixtures

The test suite uses a centralized fixture system in `test_fixtures.py`:

### JSON Test Data
- **`GENERIC_COMMENTARY_BLOCKCOMMENTS_ENTRY`**: Generic entry with two svgGroupIds for reuse across unit tests
- **`GENERIC_COMMENTARY_BLOCKCOMMENTS_ENTRY_MULTIPLE`**: Generic entry with multiple comment blocks
- **`JSON_DATA_WITH_SINGLE_PREFIXED_ID`**: Single correctly updated ID
- **`JSON_DATA_WITH_2_PREFIXED_IDS`**: Two correctly updated IDs  
- **`JSON_DATA_WITH_4_PREFIXED_IDS`**: Four correctly updated IDs
- **`JSON_DATA_WITH_TODO`**: Contains TODO entries (should be ignored)
- **`JSON_DATA_WITH_TODO_AND_MIXED_IDS`**: TODO entries combined with mixed prefixed/unprefixed IDs
- **`JSON_DATA_WITH_MIXED_IDS`**: Mix of updated and unchanged IDs
- **`JSON_DATA_WITH_MULTIPLE_MIXED_IDS`**: Multiple entries with mixed prefixed/unprefixed IDs
- **`JSON_DATA_INTEGRATION`**: Multi-entry structure used for integration-style tests
- **`JSON_DATA_MULTIPLE_ENTRIES`**: Multiple textcritics entries for multi-entry processing tests
- **`JSON_DATA_EMPTY`**: Empty data structure
- **`JSON_DATA_MALFORMED`**: Invalid JSON for error testing

### SVG Test Content  
- **Single file samples**: `SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID`, `SAMPLE_SVG_WITH_SINGLE_UNPREFIXED_ID`
- **Multiple ID samples**: `SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS`, `SAMPLE_SVG_WITH_MULTIPLE_UNPREFIXED_IDS`
- **Multi-file samples**: `SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS`, `SAMPLE_MULTIPLE_SVG_WITH_UNPREFIXED_IDS`
- **Mixed scenarios**: `SAMPLE_SVG_WITH_MIXED_IDS`, `SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS`

All test data is generated programmatically using helper functions to ensure consistency and easy maintenance.

## Continuous Integration

The test suite is designed to:
- Run in isolated environments with proper package imports
- Use centralized fixtures to avoid code duplication
- Clean up temporary files automatically
- Provide clear error messages with specific assertions
- Support parallel execution via pytest-xdist

## Adding New Tests

When adding new functionality:

1. **Add fixtures** to `test_fixtures.py` if creating shared test data
2. **Create unit tests** in the appropriate `test_<module>.py` file
3. **Add integration tests** to `test_unifiers_integration.py` for end-to-end workflows  
4. **Include edge cases** and error conditions
5. **Update this README** with new test descriptions
6. **Use helper functions** from fixtures for consistent data generation

## Example Test Run Output

```
$ pytest tests/ --cov=utils --cov=unify_link_box_ids --cov=unify_tkk_ids --cov=unify_kv_ids --cov-report=term

======== test session starts ========

tests/test_extraction_utils.py::... PASSED
tests/test_file_utils.py::... PASSED
tests/test_svg_utils.py::... PASSED
tests/test_unify_kv_ids.py::... PASSED
tests/test_unify_link_box_ids.py::... PASSED
tests/test_unify_tkk_ids.py::... PASSED
tests/test_validation_utils.py::... PASSED
...

======== 50+ passed in 3.45s ========

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
unify_tkk_ids.py                145     8    95%   187-190, 23-25
utils/__init__.py                13     0   100%
utils/extraction_utils.py        35     2    94%   45-46
utils/file_utils.py              67     3    96%   78-80
utils/svg_utils.py               89     4    96%   134-137
utils/validation_utils.py        45     1    98%   67
-----------------------------------------------------------
TOTAL                           394    18    95%
```
