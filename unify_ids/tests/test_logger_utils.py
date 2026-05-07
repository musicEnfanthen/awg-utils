#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for logger_utils.py

Tests for:
- Logger.__init__: initial stats counters
- bump_stats: incrementing counters and invalid key handling
- log: message formatting, list appending, and verbose printing
- log_processing_start: startup banner and dry-run write notice
- log_processing_entry_start: entry ID print and verbose guard
- log_processing_entry_context: standard/SkRT branches and verbose guard
- log_id_change: bump_changed flag, verbose guard, JSON/SVG output, dry-run marker
- log_id_change_json: JSON-only output line
- log_id_change_svg: SVG-only output line
- log_ids_missing: stat bump and error message
- log_ids_multiple: stat bump and warning message
- log_svg_error: stat bump and warning message
- log_svg_unchanged: stat bump and info message
- print_report: success message and error/info categorisation
- print_stats_summary: formatted summary output
"""

import unittest

from utils.logger_utils import Logger


class TestLoggerInitAndStats(unittest.TestCase):
    """Tests for Logger initialization, bump_stats, print_report, and print_stats_summary."""

    def setUp(self):
        """Set up a Logger instance for testing."""
        self.logger = Logger(verbose=False)

    def test_logger_initial_stats(self):
        """Test that all stats counters are initialized to 0."""
        expected = {
            "entries_seen": 0,
            "ids_seen": 0,
            "ids_changed": 0,
            "ids_missing": 0,
            "ids_multiple": 0,
            "ids_unchanged": 0,
            "svg_errors": 0,
            "svg_unchanged": 0,
        }
        self.assertEqual(self.logger.stats, expected)

    def test_bump_stats_and_summary(self):
        """Test that bump_stats() increments counters and summary() prints correct string."""
        self.logger.bump_stats("entries_seen")
        self.logger.bump_stats("ids_changed", 5)
        self.logger.bump_stats("svg_errors", 2)

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_stats_summary()
            printed = mock_print.call_args[0][0]
            self.assertIn("Summary:", printed)
            self.assertIn("entries=1", printed)
            self.assertIn("changed=5", printed)
            self.assertIn("svg_errors=2", printed)

    def test_bump_stats_invalid_key(self):
        """Test that bump_stats() raises KeyError for invalid stat key."""
        with self.assertRaises(KeyError):
            self.logger.bump_stats("not_a_stat")

    def test_print_stats_summary(self):
        """Test that print_stats_summary prints the labeled summary string."""
        self.logger.bump_stats("entries_seen", 2)
        self.logger.bump_stats("ids_missing", 3)

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_stats_summary()
            printed = mock_print.call_args[0][0]
            self.assertIn("Summary:", printed)
            self.assertIn("entries=2", printed)
            self.assertIn("missing=3", printed)

    def test_print_report_success(self):
        """Test that print_report() prints success message when no messages are logged."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_report()
            mock_print.assert_any_call(
                "\n [\u2713] All JSON and SVG IDs successfully updated."
            )

    def test_print_report_with_errors_and_info(self):
        """Test that print_report() correctly categorizes and prints messages."""
        self.logger.log("error", "E001", "ID1", "Error message")
        self.logger.log("info", "I001", "ID2", "Info message")

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_report()
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertTrue(
                any("--- Errors and Warnings ---" in call for call in calls)
            )
            self.assertTrue(any("--- Info Messages ---" in call for call in calls))


class TestLoggerLog(unittest.TestCase):
    """Tests for log() and log_items_found()."""

    def setUp(self):
        """Set up a Logger instance for testing."""
        self.logger = Logger(verbose=False)

    def test_log_appends_and_prints(self):
        """Test that log() appends formatted message to messages list and prints it."""
        self.logger.verbose = True

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log("error", "E001", "M143_TF1", "Something went wrong")
            expected = " [ERROR] M143_TF1: Something went wrong [E001]"
            self.assertIn(expected, self.logger.messages)
            mock_print.assert_called_with(expected)

    def test_log_without_entry_id_and_code(self):
        """Test log() behavior when entry_id and code are empty."""
        self.logger.log("warning", "", "", "something happened")
        expected = " [WARNING] something happened"
        self.assertIn(expected, self.logger.messages)

    def test_log_items_found_count_svg_group_ids(self):
        """Test that log_items_found() prints count when svgGroupIds are present."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_items_found(["a", "b"], "svgGroupIds")
            mock_print.assert_called_once_with(" Found 2 svgGroupIds to process")

    def test_log_items_found_count_link_boxes(self):
        """Test that log_items_found() prints count when linkBoxes are present."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_items_found(
                [{"svgGroupId": "g1"}, {"svgGroupId": "g2"}], "linkBoxes"
            )
            mock_print.assert_called_once_with(" Found 2 linkBoxes to process")

    def test_log_items_found_absent_svg_group_ids(self):
        """Test that log_items_found() prints absence message when svgGroupIds is empty."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_items_found([], "svgGroupIds")
            mock_print.assert_called_once_with(" No svgGroupIds to process")

    def test_log_items_found_absent_link_boxes(self):
        """Test that log_items_found() prints absence message when linkBoxes is empty."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_items_found([], "linkBoxes")
            mock_print.assert_called_once_with(" No linkBoxes to process")

    def test_log_items_found_silent_when_not_verbose(self):
        """Test that log_items_found() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_items_found(["x"], "svgGroupIds")
            mock_print.assert_not_called()


class TestLoggerProcessing(unittest.TestCase):
    """Tests for log_processing_start, log_processing_entry_start,
    log_processing_entry_context."""

    def setUp(self):
        """Set up a Logger instance for testing."""
        self.logger = Logger(verbose=False)

    def test_log_processing_entry_start_prints_when_verbose(self):
        """Test that log_processing_entry_start() prints the entry ID when verbose."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_entry_start("M143_TF1")
            mock_print.assert_called_once_with(
                "\nProcessing textcritics entry ID: M143_TF1"
            )

    def test_log_processing_entry_start_silent_when_not_verbose(self):
        """Test that log_processing_entry_start() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_entry_start("M143_TF1")
            mock_print.assert_not_called()

    def test_log_processing_start_prints_banner_only_when_not_dry_run(self):
        """Test that log_processing_start() prints only the start banner when dry_run is False."""
        self.logger.verbose = True
        self.logger.dry_run = False
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_start("TKK ID")
            mock_print.assert_called_once_with("--- Starting TKK ID processing ---")

    def test_log_processing_start_prints_banner_and_dry_run_notice(self):
        """Test that log_processing_start() prints dry-run notice when dry_run is True."""
        self.logger.verbose = True
        self.logger.dry_run = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_start("Link Box ID")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn("--- Starting Link Box ID processing ---", calls)
            self.assertIn(" [DRY-RUN] No files will be written.", calls)

    def test_log_processing_start_silent_when_not_verbose(self):
        """Test that log_processing_start() prints nothing when verbose is False."""
        self.logger.verbose = False
        self.logger.dry_run = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_start("TKK ID")
            mock_print.assert_not_called()

    def test_log_processing_entry_context_standard(self):
        """Test log_processing_entry_context() prints standard anchor and SVG list when verbose."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_entry_context("M143_TF1", ["a.svg", "b.svg"])
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn(" Standard anchor: M143_TF1", calls)
            self.assertIn(" Relevant SVGs (2): ['a.svg', 'b.svg']", calls)

    def test_log_processing_entry_context_skrt(self):
        """Test log_processing_entry_context() prints SkRT anchor when entry_id contains 'SkRT'."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_entry_context("M143_SkRT1", ["x.svg"])
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn(" SkRT anchor detected: M143_SkRT1", calls)

    def test_log_processing_entry_context_silent_when_not_verbose(self):
        """Test log_processing_entry_context() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_processing_entry_context("M143_TF1", ["a.svg"])
            mock_print.assert_not_called()


class TestLoggerIdChange(unittest.TestCase):
    """Tests for log_id_change, log_id_change_json, and log_id_change_svg,
    log_ids_missing, log_ids_multiple, log_svg_error, and log_svg_unchanged."""

    def setUp(self):
        """Set up a Logger instance for testing."""
        self.logger = Logger(verbose=False)

    def test_log_id_change_bumps_stat(self):
        """Test that log_id_change() increments ids_changed when bump_changed=True."""
        self.logger.log_id_change("old-id", "new-id", "file.svg")
        self.assertEqual(self.logger.stats["ids_changed"], 1)

    def test_log_id_change_silent_when_not_verbose(self):
        """Test that log_id_change() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change("old-id", "new-id", "file.svg")
            mock_print.assert_not_called()

    def test_log_id_change_prints_json_and_svg(self):
        """Test that log_id_change() prints JSON and SVG lines when verbose."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change("old-id", "new-id", "file.svg")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn(" [JSON] Changing 'old-id' -> 'new-id'", calls)
            self.assertIn(" [SVG]  Changing 'old-id' -> 'new-id' in file.svg", calls)

    def test_log_id_change_dry_run_marker(self):
        """Test that log_id_change() prefixes lines with [DRY-RUN] when dry_run=True."""
        self.logger.verbose = True
        self.logger.dry_run = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change("old-id", "new-id", "file.svg")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertTrue(any("[DRY-RUN]" in c for c in calls))

    def test_log_id_change_json_prints_json_only(self):
        """Test that log_id_change_json() prints only the JSON line when verbose."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_json("old-id", "new-id")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn(" [JSON] Changing 'old-id' -> 'new-id'", calls)
            self.assertFalse(any("[SVG]" in c for c in calls))

    def test_log_id_change_json_silent_when_not_verbose(self):
        """Test that log_id_change_json() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_json("old-id", "new-id")
            mock_print.assert_not_called()

    def test_log_id_change_json_dry_run_marker(self):
        """Test that log_id_change_json() prefixes output with [DRY-RUN] when dry_run=True."""
        self.logger.verbose = True
        self.logger.dry_run = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_json("old-id", "new-id")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertTrue(any("[DRY-RUN]" in c for c in calls))

    def test_log_id_change_svg_prints_svg_only(self):
        """Test that log_id_change_svg() prints only the SVG line when verbose."""
        self.logger.verbose = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_svg("old-id", "new-id", "file.svg")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertIn(" [SVG]  Changing 'old-id' -> 'new-id' in file.svg", calls)
            self.assertFalse(any("[JSON]" in c for c in calls))

    def test_log_id_change_svg_silent_when_not_verbose(self):
        """Test that log_id_change_svg() prints nothing when verbose is False."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_svg("old-id", "new-id", "file.svg")
            mock_print.assert_not_called()

    def test_log_id_change_svg_dry_run_marker(self):
        """Test that log_id_change_svg() prefixes output with [DRY-RUN] when dry_run=True."""
        self.logger.verbose = True
        self.logger.dry_run = True
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log_id_change_svg("old-id", "new-id", "file.svg")
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertTrue(any("[DRY-RUN]" in c for c in calls))

    def test_log_ids_missing(self):
        """Test that log_ids_missing() bumps ids_missing stat and logs an error."""
        self.logger.log_ids_missing("M143_TF1", "old-id", "awg-tkk")
        self.assertEqual(self.logger.stats["ids_missing"], 1)
        expected = (
            " [ERROR] M143_TF1: 'old-id' with class 'awg-tkk'"
            " not found in any relevant SVG files [ids_missing]"
        )
        self.assertIn(expected, self.logger.messages)

    def test_log_ids_multiple(self):
        """Test that log_ids_multiple() bumps ids_multiple stat and logs a warning."""
        self.logger.log_ids_multiple("M143_TF1", "old-id", ["a.svg", "b.svg"])
        self.assertEqual(self.logger.stats["ids_multiple"], 1)
        expected = (
            " [WARNING] M143_TF1: 'old-id' found in 2 files: ['a.svg', 'b.svg'];"
            " skipping — manual review required [ids_multiple]"
        )
        self.assertIn(expected, self.logger.messages)

    def test_log_svg_error(self):
        """Test that log_svg_error() bumps svg_errors stat and logs a warning."""
        self.logger.log_svg_error("M143_TF1", "old-id", "file.svg", "some error")
        self.assertEqual(self.logger.stats["svg_errors"], 1)
        expected = (
            " [WARNING] M143_TF1: Could not update 'old-id' in file.svg;"
            " JSON unchanged (some error) [svg_errors]"
        )
        self.assertIn(expected, self.logger.messages)

    def test_log_svg_unchanged(self):
        """Test that log_svg_unchanged() bumps svg_unchanged stat and logs an info message."""
        self.logger.log_svg_unchanged("M143_TF1", "new-id", "file.svg")
        self.assertEqual(self.logger.stats["svg_unchanged"], 1)
        expected = (
            " [INFO] M143_TF1: SVG already had 'new-id' in file.svg;"
            " updating JSON only [svg_unchanged]"
        )
        self.assertIn(expected, self.logger.messages)


if __name__ == "__main__":
    unittest.main()
