#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for unify_kv_ids.py

Tests for KV (Korrektur-Verzeichnis) ID unification functionality including:
- Entry part derivation from correction IDs and complex IDs
- Sequential ID assignment across flat/grouped blockComments
- JSON mutation (in-place, svgGroupId in first position)
- Dry-run behaviour
- Idempotency (second run is a no-op)
- Main function error handling
- Delegation: higher-level functions call the correct sub-functions
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, call

import pytest

from unify_kv_ids import (
    _derive_entry_part,
    process_correction_entry,
    process_kv_ids_per_correction,
    unify_kv_ids,
    main,
)
from utils.constants import KV
from utils.logger_utils import Logger


def _make_block_comment(svg_group_id="", **extra):
    """Return a minimal blockComment dict."""
    bc = {"svgGroupId": svg_group_id}
    bc.update(extra)
    return bc


def _make_correction(corr_id, block_comments_per_group):
    """Return a correction dict with one or more blockHeader groups.

    Args:
        corr_id (str): The correction 'id' value.
        block_comments_per_group (list[list[dict]]): Each inner list is the
            blockComments for one comment group.
    """
    comments = [
        {"blockHeader": "", "blockComments": bcs}
        for bcs in block_comments_per_group
    ]
    return {
        "id": corr_id,
        "commentary": {"preamble": "", "comments": comments},
    }


def _make_source_json(corrections):
    """Wrap corrections inside a minimal source-description structure."""
    return {
        "sources": [
            {"id": "source_E", "physDesc": {"corrections": corrections}}
        ]
    }


def _logger(**kwargs):
    return Logger(verbose=False, **kwargs)


@pytest.mark.unit
class TestDeriveEntryPart(unittest.TestCase):
    """Tests for _derive_entry_part."""

    def test_source_prefix_is_replaced_by_complex_id(self):
        """'source_E_corr_1' with 'op25' -> 'op25_E_corr_1'."""
        result = _derive_entry_part("source_E_corr_1", "op25")
        self.assertEqual(result, "op25_E_corr_1")

    def test_source_prefix_stripped_for_corr_2(self):
        """'source_E_corr_2' with 'op25' -> 'op25_E_corr_2'."""
        result = _derive_entry_part("source_E_corr_2", "op25")
        self.assertEqual(result, "op25_E_corr_2")

    def test_different_complex_id(self):
        """Works with any complex_id, e.g. 'm317'."""
        result = _derive_entry_part("source_E_corr_1", "m317")
        self.assertEqual(result, "m317_E_corr_1")

    def test_non_source_id_gets_underscore_prefix(self):
        """ID not starting with 'source' gets an underscore separator."""
        result = _derive_entry_part("custom_corr", "op25")
        self.assertEqual(result, "op25_custom_corr")


@pytest.mark.unit
class TestProcessKvIdsPerCorrection(unittest.TestCase):
    """Tests for process_kv_ids_per_correction."""

    def _run(self, comments_list, entry_part="op25_E_corr_1", **logger_kwargs):
        logger = _logger(**logger_kwargs)
        process_kv_ids_per_correction("source_E_corr_1", entry_part, comments_list, logger)
        return logger

    def test_single_block_comment_gets_id_001(self):
        """A single blockComment receives the -001 suffix."""
        bc = _make_block_comment()
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list)
        self.assertEqual(bc["svgGroupId"], f"{KV.prefix}op25_E_corr_1-001")

    def test_sequential_ids_across_single_group(self):
        """Multiple blockComments in one group get 001, 002, 003."""
        bcs = [_make_block_comment() for _ in range(3)]
        comments_list = [{"blockHeader": "", "blockComments": bcs}]
        self._run(comments_list)
        for i, bc in enumerate(bcs, start=1):
            self.assertEqual(bc["svgGroupId"], f"{KV.prefix}op25_E_corr_1-{i:03d}")

    def test_counter_is_flat_across_multiple_groups(self):
        """Counter continues across blockHeader groups (no reset)."""
        group1 = [_make_block_comment(), _make_block_comment()]
        group2 = [_make_block_comment(), _make_block_comment()]
        comments_list = [
            {"blockHeader": "Group 1", "blockComments": group1},
            {"blockHeader": "Group 2", "blockComments": group2},
        ]
        self._run(comments_list)
        all_bcs = group1 + group2
        for i, bc in enumerate(all_bcs, start=1):
            self.assertEqual(bc["svgGroupId"], f"{KV.prefix}op25_E_corr_1-{i:03d}")

    def test_already_correct_id_is_not_changed(self):
        """blockComment whose svgGroupId already matches is left unchanged."""
        expected_id = f"{KV.prefix}op25_E_corr_1-001"
        bc = _make_block_comment(svg_group_id=expected_id, measure="1")
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        logger = self._run(comments_list)
        self.assertEqual(bc["svgGroupId"], expected_id)
        self.assertEqual(logger.stats["ids_unchanged"], 1)
        self.assertEqual(logger.stats["ids_changed"], 0)

    def test_second_run_is_noop(self):
        """Running twice results in no additional changes on the second run."""
        bc = _make_block_comment()
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list)
        logger2 = self._run(comments_list)
        self.assertEqual(logger2.stats["ids_changed"], 0)
        self.assertEqual(logger2.stats["ids_unchanged"], 1)

    def test_dry_run_does_not_mutate_block_comment(self):
        """In dry-run mode the blockComment dict is not modified."""
        bc = _make_block_comment()
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list, dry_run=True)
        self.assertEqual(bc["svgGroupId"], "")

    def test_dry_run_still_bumps_stats(self):
        """ids_changed stat is still incremented during dry-run."""
        bc = _make_block_comment()
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        logger = self._run(comments_list, dry_run=True)
        self.assertEqual(logger.stats["ids_changed"], 1)

    def test_svg_group_id_is_first_key_after_update(self):
        """svgGroupId must be the first key in the mutated dict."""
        bc = _make_block_comment(measure="1", system="Ges.", position="2/4")
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list)
        self.assertEqual(list(bc.keys())[0], "svgGroupId")

    def test_other_keys_are_preserved_after_update(self):
        """Existing keys other than svgGroupId are retained unchanged."""
        bc = _make_block_comment(measure="3", system="Klav.", position="1/8",
                                 comment="Some text")
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list)
        self.assertEqual(bc["measure"], "3")
        self.assertEqual(bc["system"], "Klav.")
        self.assertEqual(bc["position"], "1/8")
        self.assertEqual(bc["comment"], "Some text")

    def test_mutation_is_in_place(self):
        """The original dict object is mutated, not replaced."""
        bc = _make_block_comment()
        original_id = id(bc)
        comments_list = [{"blockHeader": "", "blockComments": [bc]}]
        self._run(comments_list)
        self.assertEqual(id(bc), original_id)

    def test_ids_seen_is_incremented_per_block_comment(self):
        """ids_seen is incremented for every blockComment processed."""
        bcs = [_make_block_comment() for _ in range(4)]
        comments_list = [{"blockHeader": "", "blockComments": bcs}]
        logger = self._run(comments_list)
        self.assertEqual(logger.stats["ids_seen"], 4)


@pytest.mark.unit
class TestProcessCorrectionEntry(unittest.TestCase):
    """Tests for process_correction_entry."""

    def test_missing_id_logs_warning_and_skips(self):
        """Correction with no id is skipped with a warning."""
        correction = {"commentary": {"comments": []}}
        logger = _logger()
        with patch("builtins.print"):
            process_correction_entry(correction, "op25", logger)
        self.assertEqual(logger.stats["entries_seen"], 0)

    def test_empty_id_logs_warning_and_skips(self):
        """Correction with empty string id is skipped."""
        correction = {"id": "", "commentary": {"comments": []}}
        logger = _logger()
        with patch("builtins.print"):
            process_correction_entry(correction, "op25", logger)
        self.assertEqual(logger.stats["entries_seen"], 0)

    def test_valid_correction_bumps_entries_seen(self):
        """Valid correction increments entries_seen."""
        bc = _make_block_comment()
        correction = _make_correction("source_E_corr_1", [[bc]])
        logger = _logger()
        process_correction_entry(correction, "op25", logger)
        self.assertEqual(logger.stats["entries_seen"], 1)

    def test_calls_derive_entry_part(self):
        """Delegates to _derive_entry_part with correction_id and complex_id."""
        bc = _make_block_comment()
        correction = _make_correction("source_E_corr_1", [[bc]])
        with patch("unify_kv_ids._derive_entry_part", return_value="op25_E_corr_1") as mock_derive:
            process_correction_entry(correction, "op25", _logger())
        mock_derive.assert_called_once_with("source_E_corr_1", "op25")

    def test_calls_process_kv_ids_per_correction(self):
        """Delegates to process_kv_ids_per_correction with correct arguments."""
        bc = _make_block_comment()
        correction = _make_correction("source_E_corr_1", [[bc]])
        logger = _logger()
        with patch("unify_kv_ids.process_kv_ids_per_correction") as mock_proc:
            process_correction_entry(correction, "op25", logger)
        expected_comments = correction["commentary"]["comments"]
        mock_proc.assert_called_once_with(
            "source_E_corr_1", "op25_E_corr_1", expected_comments, logger
        )

    def test_passes_derived_entry_part_downstream(self):
        """Passes the return value of _derive_entry_part to process_kv_ids_per_correction."""
        bc = _make_block_comment()
        correction = _make_correction("source_E_corr_1", [[bc]])
        logger = _logger()
        with patch("unify_kv_ids._derive_entry_part", return_value="custom_part"), \
             patch("unify_kv_ids.process_kv_ids_per_correction") as mock_proc:
            process_correction_entry(correction, "op25", logger)
        _, entry_part_arg, *_ = mock_proc.call_args[0]
        self.assertEqual(entry_part_arg, "custom_part")

    def test_skips_delegation_for_missing_id(self):
        """No sub-function call when correction has no id."""
        correction = {"commentary": {"comments": []}}
        with patch("unify_kv_ids.process_kv_ids_per_correction") as mock_proc, \
             patch("builtins.print"):
            process_correction_entry(correction, "op25", _logger())
        mock_proc.assert_not_called()

    def test_skips_delegation_for_empty_comments(self):
        """No call to process_kv_ids_per_correction when comments list is empty."""
        correction = {"id": "source_E_corr_1", "commentary": {"comments": []}}
        with patch("unify_kv_ids.process_kv_ids_per_correction") as mock_proc:
            process_correction_entry(correction, "op25", _logger())
        mock_proc.assert_not_called()

    def test_empty_comments_list_returns_early(self):
        """Correction with empty comments list produces no ID changes."""
        correction = {"id": "source_E_corr_1", "commentary": {"comments": []}}
        logger = _logger()
        process_correction_entry(correction, "op25", logger)
        self.assertEqual(logger.stats["ids_changed"], 0)


@pytest.mark.integration
class TestUnifyKvIds(unittest.TestCase):
    """Integration tests for unify_kv_ids writing to a real temp directory."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "source-description.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write_json(self, data):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")

    def _read_json(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_raw(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            return f.read()

    # --- error handling ---

    def test_missing_json_raises_file_not_found(self):
        """Raises FileNotFoundError when the JSON path does not exist."""
        with self.assertRaises(FileNotFoundError):
            unify_kv_ids("/nonexistent/path.json", "op25", _logger())

    def test_corrections_without_svg_group_id_receive_ids(self):
        """blockComments missing svgGroupId get sequential IDs written to JSON."""
        bc1 = {"measure": "1", "comment": "first"}
        bc2 = {"measure": "2", "comment": "second"}
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc1, bc2]])])
        self._write_json(data)

        result = unify_kv_ids(self.json_path, "op25", _logger())

        self.assertTrue(result)
        updated = self._read_json()
        bcs = updated["sources"][0]["physDesc"]["corrections"][0][
            "commentary"]["comments"][0]["blockComments"]
        self.assertEqual(bcs[0]["svgGroupId"], f"{KV.prefix}op25_E_corr_1-001")
        self.assertEqual(bcs[1]["svgGroupId"], f"{KV.prefix}op25_E_corr_1-002")

    def test_counter_resets_between_corrections(self):
        """Each correction has its own counter starting at 001."""
        bc_a = _make_block_comment()
        bc_b = _make_block_comment()
        corr1 = _make_correction("source_E_corr_1", [[bc_a]])
        corr2 = _make_correction("source_E_corr_2", [[bc_b]])
        data = _make_source_json([corr1, corr2])
        self._write_json(data)

        unify_kv_ids(self.json_path, "op25", _logger())

        updated = self._read_json()
        corrections = updated["sources"][0]["physDesc"]["corrections"]
        id1 = corrections[0]["commentary"]["comments"][0]["blockComments"][0]["svgGroupId"]
        id2 = corrections[1]["commentary"]["comments"][0]["blockComments"][0]["svgGroupId"]
        self.assertEqual(id1, f"{KV.prefix}op25_E_corr_1-001")
        self.assertEqual(id2, f"{KV.prefix}op25_E_corr_2-001")

    def test_no_changes_detected_skips_write(self):
        """When all IDs are already correct, the file is not rewritten."""
        bc = {"svgGroupId": f"{KV.prefix}op25_E_corr_1-001", "measure": "1"}
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)
        mtime_before = os.path.getmtime(self.json_path)

        unify_kv_ids(self.json_path, "op25", _logger())

        mtime_after = os.path.getmtime(self.json_path)
        self.assertEqual(mtime_before, mtime_after)

    def test_dry_run_does_not_write_file(self):
        """dry_run=True never modifies the JSON file on disk."""
        bc = _make_block_comment()
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)
        raw_before = self._read_raw()

        unify_kv_ids(self.json_path, "op25", _logger(dry_run=True))

        self.assertEqual(raw_before, self._read_raw())

    def test_verbose_prints_no_changes_message_when_all_ids_already_correct(self):
        """Verbose mode prints 'No changes detected' when nothing needs updating."""
        bc = {"svgGroupId": f"{KV.prefix}op25_E_corr_1-001", "measure": "1"}
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)

        with patch("builtins.print") as mock_print:
            unify_kv_ids(self.json_path, "op25", Logger(verbose=True))

        printed = [c[0][0] for c in mock_print.call_args_list if c[0]]
        self.assertTrue(any("No changes detected" in msg for msg in printed))

    def test_verbose_prints_dry_run_skip_message(self):
        """Verbose dry-run mode prints '[DRY-RUN] Skipping write.'."""
        bc = _make_block_comment()
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)

        with patch("builtins.print") as mock_print:
            unify_kv_ids(self.json_path, "op25", Logger(verbose=True, dry_run=True))

        printed = [c[0][0] for c in mock_print.call_args_list if c[0]]
        self.assertTrue(any("DRY-RUN" in msg and "Skipping write" in msg for msg in printed))

    def test_verbose_prints_stats_summary(self):
        """Verbose mode prints a stats summary line after processing."""
        bc = _make_block_comment()
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)

        with patch("builtins.print") as mock_print:
            unify_kv_ids(self.json_path, "op25", Logger(verbose=True))

        printed = [c[0][0] for c in mock_print.call_args_list if c[0]]
        self.assertTrue(any("Summary:" in msg for msg in printed))

    def test_second_run_is_noop(self):
        """Running unify_kv_ids twice yields identical JSON."""
        bc = _make_block_comment()
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)

        unify_kv_ids(self.json_path, "op25", _logger())
        raw_after_first = self._read_raw()

        unify_kv_ids(self.json_path, "op25", _logger())
        raw_after_second = self._read_raw()

        self.assertEqual(raw_after_first, raw_after_second)

    def test_svg_group_id_is_first_key_in_written_json(self):
        """After writing, svgGroupId is serialized as the first key."""
        bc = {"measure": "1", "system": "Ges.", "position": "", "comment": "text"}
        data = _make_source_json([_make_correction("source_E_corr_1", [[bc]])])
        self._write_json(data)

        unify_kv_ids(self.json_path, "op25", _logger())

        raw = self._read_raw()
        # svgGroupId must appear before any of the other original keys
        idx_svg = raw.find('"svgGroupId"')
        idx_measure = raw.find('"measure"')
        self.assertLess(idx_svg, idx_measure)

    def test_corrections_across_multiple_sources_are_all_processed(self):
        """Corrections in more than one source entry are each updated."""
        bc_a = _make_block_comment()
        bc_b = _make_block_comment()
        data = {
            "sources": [
                {"id": "source_A", "physDesc": {
                    "corrections": [_make_correction("source_A_corr_1", [[bc_a]])]
                }},
                {"id": "source_B", "physDesc": {
                    "corrections": [_make_correction("source_B_corr_1", [[bc_b]])]
                }},
            ]
        }
        self._write_json(data)

        unify_kv_ids(self.json_path, "op25", _logger())

        updated = self._read_json()
        id_a = updated["sources"][0]["physDesc"]["corrections"][0][
            "commentary"]["comments"][0]["blockComments"][0]["svgGroupId"]
        id_b = updated["sources"][1]["physDesc"]["corrections"][0][
            "commentary"]["comments"][0]["blockComments"][0]["svgGroupId"]
        self.assertEqual(id_a, f"{KV.prefix}op25_A_corr_1-001")
        self.assertEqual(id_b, f"{KV.prefix}op25_B_corr_1-001")

    def test_calls_process_correction_entry_for_each_correction(self):
        """Delegates to process_correction_entry once per correction."""
        corr1 = _make_correction("source_E_corr_1", [[_make_block_comment()]])
        corr2 = _make_correction("source_E_corr_2", [[_make_block_comment()]])
        data = _make_source_json([corr1, corr2])
        self._write_json(data)
        logger = _logger()
        with patch("unify_kv_ids.process_correction_entry") as mock_pce, \
             patch("builtins.print"):
            unify_kv_ids(self.json_path, "op25", logger)
        self.assertEqual(mock_pce.call_count, 2)
        calls = mock_pce.call_args_list
        self.assertEqual(calls[0], call(corr1, "op25", logger))
        self.assertEqual(calls[1], call(corr2, "op25", logger))

    def test_passes_complex_id_to_process_correction_entry(self):
        """Forwards complex_id unchanged to process_correction_entry."""
        corr = _make_correction("source_E_corr_1", [[_make_block_comment()]])
        self._write_json(_make_source_json([corr]))
        with patch("unify_kv_ids.process_correction_entry") as mock_pce, \
             patch("builtins.print"):
            unify_kv_ids(self.json_path, "m317", _logger())
        _, complex_id_arg, _ = mock_pce.call_args[0]
        self.assertEqual(complex_id_arg, "m317")


@pytest.mark.unit
class TestMain(unittest.TestCase):
    """Tests for main."""

    def setUp(self):
        self.unify_kv_ids_patcher = patch("unify_kv_ids.unify_kv_ids")
        self.mock_unify_kv_ids = self.unify_kv_ids_patcher.start()
        self.mock_unify_kv_ids.return_value = True

        self.exit_patcher = patch("sys.exit")
        self.mock_exit = self.exit_patcher.start()

    def tearDown(self):
        self.unify_kv_ids_patcher.stop()
        self.exit_patcher.stop()

    def test_main_success_path(self):
        """Test main on successful processing."""
        with patch("builtins.print") as mock_print:
            main()
        self.mock_unify_kv_ids.assert_called_once()
        _, _, logger = self.mock_unify_kv_ids.call_args[0]
        self.assertIsInstance(logger, Logger)
        self.assertFalse(logger.dry_run)
        self.assertTrue(logger.verbose)
        mock_print.assert_called_once_with("\n Finished!")
        self.mock_exit.assert_not_called()

    def test_main_with_warnings(self):
        """Test main when unify_kv_ids returns False."""
        self.mock_unify_kv_ids.return_value = False
        with patch("builtins.print") as mock_print:
            main()
        self.mock_unify_kv_ids.assert_called_once()
        mock_print.assert_called_once_with("\n Processing completed with warnings.")
        self.mock_exit.assert_not_called()

    def test_main_file_not_found_error(self):
        """Test main exits with code 1 on FileNotFoundError."""
        self.mock_unify_kv_ids.side_effect = FileNotFoundError("missing file")
        with patch("builtins.print") as mock_print:
            main()
        mock_print.assert_called_once_with("Error: missing file")
        self.mock_exit.assert_called_once_with(1)

    def test_main_unexpected_error(self):
        """Test main exits with code 1 on unexpected exception."""
        self.mock_unify_kv_ids.side_effect = ValueError("bad value")
        with patch("builtins.print") as mock_print:
            main()
        mock_print.assert_called_once_with("Unexpected error: bad value")
        self.mock_exit.assert_called_once_with(1)

    def test_main_configuration_values(self):
        """Test main passes correct configuration to unify_kv_ids."""
        with patch("builtins.print"):
            main()
        json_path, complex_id, logger = self.mock_unify_kv_ids.call_args[0]
        self.assertEqual(json_path, "./tests/data/source-description.json")
        self.assertEqual(complex_id, "op25")
        self.assertIsInstance(logger, Logger)
        self.assertFalse(logger.dry_run)
        self.assertTrue(logger.verbose)
