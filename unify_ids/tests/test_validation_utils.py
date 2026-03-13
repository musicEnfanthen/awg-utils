#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for validation_utils.py module

This test suite provides comprehensive testing for the validation utilities
used in TKK ID processing.

Test Categories:
- display_validation_report function tests (main validation reporting)
- validate_json_entries function tests
- validate_svg_entries function tests
- Edge cases and error conditions

Usage:
    python -m pytest tests/test_validation_utils.py -v
    python -m pytest tests/test_validation_utils.py::TestDisplayValidationReport -v
"""

import unittest
from unittest.mock import patch
from io import StringIO
import pytest

# Import validation functions from utils.validation_utils
from utils.validation_utils import (
    display_validation_report,
    validate_json_entries,
    validate_svg_entries
)

# Import shared test fixtures
from tests.test_fixtures import (
    JSON_DATA_WITH_SINGLE_PREFIXED_ID,
    JSON_DATA_WITH_2_PREFIXED_IDS,
    JSON_DATA_WITH_4_PREFIXED_IDS,
    JSON_DATA_WITH_TODO,
    JSON_DATA_WITH_TODO_AND_MIXED_IDS,
    JSON_DATA_EMPTY,
    JSON_DATA_MALFORMED,
    JSON_DATA_WITH_MIXED_IDS,
    JSON_DATA_WITH_MULTIPLE_MIXED_IDS,
    SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID,
    SAMPLE_SVG_WITH_SINGLE_UNPREFIXED_ID,
    SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS,
    SAMPLE_SVG_WITH_MULTIPLE_UNPREFIXED_IDS,
    SAMPLE_SVG_WITH_MIXED_IDS,
    SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS,
    SAMPLE_MULTIPLE_SVG_WITH_UNPREFIXED_IDS,
    SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS
)


@pytest.mark.unit
class TestDisplayValidationReport(unittest.TestCase):
    """Test cases for the display_validation_report function"""

    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "awg-tkk-"

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_single_file_single_entry_no_errors(
            self, mock_stdout):
        """JSON data ids == single file SVG data with single id (no errors)"""
        data = JSON_DATA_WITH_SINGLE_PREFIXED_ID.copy()
        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)

    def test_display_validation_report_with_single_file_multiple_entries_no_errors(
            self):
        """JSON data ids == single file SVG data with multiple ids (no errors)"""
        data = JSON_DATA_WITH_2_PREFIXED_IDS.copy()
        loaded_svgs = SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS.copy()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_validation_report(data, self.prefix, loaded_svgs)
            output = mock_stdout.getvalue()
            self.assertIn(
                "All JSON and SVG 'tkk' IDs successfully updated", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_multiple_svg_files_no_errors(
            self, mock_stdout):
        """JSON data ids == multiple file SVG data ids (no errors)"""
        data = JSON_DATA_WITH_4_PREFIXED_IDS.copy()
        loaded_svgs = SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_unchanged_json_ids(
            self, mock_stdout):
        """Test with unchanged JSON IDs"""
        data = JSON_DATA_WITH_MIXED_IDS.copy()

        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("JSON ERROR: Unchanged ID 'old-id-1'", output)
        self.assertIn("Total issues found: 1", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_single_file_svg_orphans(
            self, mock_stdout):
        """JSON data ids != single file SVG data ids
        (orphan IDs with a single file)"""
        data = JSON_DATA_WITH_SINGLE_PREFIXED_ID.copy()

        loaded_svgs = SAMPLE_SVG_WITH_MIXED_IDS.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("SVG ORPHAN: ID 'old-id-1'", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_multiple_files_svg_orphans(
            self, mock_stdout):
        """JSON data ids != multiple file SVG data ids
        (orphan IDs with multiple files)"""
        data = JSON_DATA_WITH_2_PREFIXED_IDS.copy()
        loaded_svgs = SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("SVG ORPHAN: ID 'old-id-2'", output)
        self.assertIn("SVG ORPHAN: ID 'old-id-3'", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_todo_entries_ignored(self, mock_stdout):
        """JSON data with TODO entries (should be ignored)"""
        data = JSON_DATA_WITH_TODO.copy()

        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_todo_and_mixed_ids(self, mock_stdout):
        """JSON data with TODO entries and mixed unchanged IDs
        (should report only unchanged ID error)"""
        data = JSON_DATA_WITH_TODO_AND_MIXED_IDS.copy()

        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID.copy()

        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("JSON ERROR: Unchanged ID 'old-id-1'", output)
        self.assertIn("Total issues found: 1", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_empty_data(self, mock_stdout):
        """Empty JSON data and empty SVG data (should report success)"""
        display_validation_report({}, "awg-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_malformed_json(self, mock_stdout):
        """Malformed JSON data
        (should report success since validation should be skipped)"""
        data = JSON_DATA_MALFORMED.copy()

        display_validation_report(data, "awg-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)


@pytest.mark.unit
class TestValidateJsonEntries(unittest.TestCase):
    """Test cases for the validate_json_entries function"""

    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "awg-tkk-"

    def test_validate_json_entries_with_single_entry_no_errors(self):
        """Test json data with a single ID correctly prefixed"""
        data = JSON_DATA_WITH_SINGLE_PREFIXED_ID.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_json_entries_with_two_entries_no_errors(self):
        """Test json data with multiple entries all correctly prefixed"""
        data = JSON_DATA_WITH_2_PREFIXED_IDS.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_json_entries_with_four_entries_no_errors(self):
        """Test json data with multiple entries all correctly prefixed"""
        data = JSON_DATA_WITH_4_PREFIXED_IDS.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_json_entries_with_a_single_unchanged_id(self):
        """Test with a single unchanged JSON ID"""
        data = JSON_DATA_WITH_MIXED_IDS.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 1)

    def test_validate_json_entries_with_multiple_unchanged_ids(self):
        """Test with multiple unchanged JSON IDs"""
        data = JSON_DATA_WITH_MULTIPLE_MIXED_IDS.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 2)

    def test_validate_json_entries_with_todo_ignored(self):
        """Test that TODO entries are ignored"""
        data = JSON_DATA_WITH_TODO.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_json_entries_with_todo_and_mixed_ids(self):
        """Test that TODO entries are ignored even when mixed
        with unchanged IDs"""
        data = JSON_DATA_WITH_TODO_AND_MIXED_IDS.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 1)

    def test_validate_json_entries_with_empty_data(self):
        """Test with empty JSON data (should report no errors)"""
        data = JSON_DATA_EMPTY.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_json_entries_with_malformed_data(self):
        """Test with malformed JSON data
        (should report no errors since validation should be skipped)"""
        data = JSON_DATA_MALFORMED.copy()

        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)


@pytest.mark.unit
class TestValidateSvgEntries(unittest.TestCase):
    """Test cases for the validate_svg_entries function"""

    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "awg-tkk-"

    def test_validate_single_svg_entry_with_no_errors(self):
        """Test with a single SVG ID correctly prefixed"""
        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_multiple_svg_entries_with_no_errors(self):
        """Test with multiple SVG IDs correctly prefixed"""
        loaded_svgs = SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_multiple_svg_files_with_no_errors(self):
        """Test with multiple SVG IDs correctly prefixed"""
        loaded_svgs = SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 0)

    def test_validate_single_svg_file_with_single_orphans(self):
        """Test with only SVG IDs that weren't updated"""
        loaded_svgs = SAMPLE_SVG_WITH_SINGLE_UNPREFIXED_ID.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 1)

    def test_validate_single_svg_file_with_all_orphans(self):
        """Test with only SVG IDs that weren't updated"""
        loaded_svgs = SAMPLE_SVG_WITH_MULTIPLE_UNPREFIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 2)

    def test_validate_multiple_svg_files_with_all_orphans(self):
        """Test with only SVG IDs that weren't updated"""
        loaded_svgs = SAMPLE_MULTIPLE_SVG_WITH_UNPREFIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 4)

    def test_validate_single_svg_file_with_mixed_results(self):
        """Test single SVG file with mix of updated and non-updated IDs"""
        loaded_svgs = SAMPLE_SVG_WITH_MIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 1)

    def test_validate_multiple_svg_files_with_mixed_results(self):
        """Test multiple SVG files with mix of updated and non-updated IDs"""
        loaded_svgs = SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS.copy()

        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 2)


# ---- shared validation coverage: TKK + LinkBox ----
import inspect
import pytest
import utils.validation_utils as _validation_utils


def _call_validate_svg_entries(loaded_svgs, prefix, required_class):
    sig = inspect.signature(_validation_utils.validate_svg_entries)
    if "required_class" in sig.parameters:
        return _validation_utils.validate_svg_entries(
            loaded_svgs, prefix, required_class=required_class
        )
    if required_class != "tkk":
        pytest.fail("validate_svg_entries must support LinkBox class filtering.")
    return _validation_utils.validate_svg_entries(loaded_svgs, prefix)


@pytest.mark.parametrize(
    "prefix,required_class",
    [("awg-tkk-", "tkk"), ("awg-lb-", "link-box")],
    ids=["tkk", "linkbox"],
)
def test_shared_validate_json_and_svg_support_both_unifiers(prefix, required_class):
    data = {
        "textcritics": [
            {
                "id": "E1",
                "commentary": {"comments": [{"blockComments": [{"svgGroupId": "old-id"}]}]},
            }
        ]
    }
    assert _validation_utils.validate_json_entries(data, prefix) == 1

    loaded_svgs = {
        "sheet.svg": {
            "content": (
                f"<g class='x {required_class} y' id='old-id'></g>"
                f"<g id='{prefix}123' class='{required_class}'></g>"
            )
        }
    }
    assert _call_validate_svg_entries(loaded_svgs, prefix, required_class) == 1
