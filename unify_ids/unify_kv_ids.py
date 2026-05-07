#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unify KV (Korrektur-Verzeichnis) IDs - Pure Python Script

For each correction entry in a source description JSON file,
assigns sequential svgGroupIds to all blockComments.

Naming scheme: awg-kv-{complex_id}_{corr_suffix}-{counter:03d}
  e.g. awg-kv-op25_E_corr_1-001

The corr_suffix is derived from the correction's 'id' field by stripping
the leading 'source' prefix (e.g. 'source_E_corr_1' -> '_E_corr_1').

No SVG files are modified; only the source description JSON is updated.
"""

import sys

from utils.constants import KV
from utils.file_utils import load_json_file, save_json_file
from utils.logger_utils import Logger


def _derive_entry_part(correction_id, complex_id):
    """Derive the ID entry part from a correction ID and a complex id.

    Strips the leading 'source' token from the correction ID and prepends
    the complex id so that e.g. 'source_E_corr_1' with complex id 'op25'
    becomes 'op25_E_corr_1'.

    Args:
        correction_id (str): Correction ID from the JSON, e.g. 'source_E_corr_1'.
        complex_id (str): Complex identifier, e.g. 'op25' or 'm317'.

    Returns:
        str: Combined entry part, e.g. 'op25_E_corr_1'.
    """
    if correction_id.startswith("source"):
        suffix = correction_id[len("source"):]
    else:
        suffix = f"_{correction_id}"
    return f"{complex_id}{suffix}"


def process_kv_ids_per_correction(correction_id, entry_part, comments_list, logger):
    """Assign sequential svgGroupIds to every blockComment in a correction.

    The counter is flat and continuous across all blockHeader groups within
    one correction entry.  It always increments for every blockComment,
    whether a change is made or the value is already correct.

    Args:
        correction_id (str): Correction ID used in log messages.
        entry_part (str): Combined complex_id + corr_suffix, e.g. 'op25_E_corr_1'.
        comments_list (list): Value of commentary.comments for this correction.
        logger (Logger): Logger instance for reporting.
    """
    counter = 1
    for comment_group in comments_list:
        for block_comment in comment_group.get("blockComments", []):
            logger.bump_stats("ids_seen")

            old_id = block_comment.get("svgGroupId", "")
            new_id = f"{KV.prefix}{entry_part}-{counter:03d}"

            if old_id == new_id:
                logger.bump_stats("ids_unchanged")
                logger.log(
                    "info",
                    "unchanged",
                    correction_id,
                    f"'{new_id}' already set; skipping",
                )
            else:
                logger.bump_stats("ids_changed")
                logger.log_id_change_json(old_id, new_id)
                if not logger.dry_run:
                    items = [(k, v) for k, v in block_comment.items() if k != "svgGroupId"]
                    items.insert(0, ("svgGroupId", new_id))
                    block_comment.clear()
                    block_comment.update(items)

            counter += 1


def process_correction_entry(correction, complex_id, logger):
    """Process all blockComments in a single correction entry.

    Args:
        correction (dict): The correction entry dict from the JSON.
        complex_id (str): Complex identifier, e.g. 'op25' or 'm317'.
        logger (Logger): Logger instance for reporting.
    """
    correction_id = correction.get("id") or ""
    if not correction_id:
        logger.log("warning", "missing_id", "", "Correction entry has no 'id'; skipping")
        return

    logger.bump_stats("entries_seen")
    logger.log_processing_entry_start(correction_id)


    comments_list = correction.get("commentary", {}).get("comments", [])
    logger.log_items_found(comments_list, "blockComments groups")
    if not comments_list:
        return

    entry_part = _derive_entry_part(correction_id, complex_id)
    process_kv_ids_per_correction(correction_id, entry_part, comments_list, logger)


def unify_kv_ids(json_path, complex_id, logger):
    """Unify KV IDs in a source description JSON file.

    Iterates over every correction entry in every source, assigns sequential
    svgGroupIds to each blockComment, and saves the updated JSON when changes
    are detected.

    Args:
        json_path (str): Path to the source description JSON file.
        complex_id (str): Complex identifier prepended to each ID, e.g. 'op25'.
        logger (Logger): Logger instance for reporting.

    Returns:
        bool: True if processing completed successfully.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
    """
    logger.log_processing_start("KV ID")

    json_data = load_json_file(json_path)
    sources = json_data.get("sources", [])
    print(f"Loaded JSON with {len(sources)} source(s)")

    for source in sources:
        corrections = source.get("physDesc", {}).get("corrections", [])
        for correction in corrections:
            process_correction_entry(correction, complex_id, logger)

    if not logger.dry_run:
        if logger.stats["ids_changed"] > 0:
            save_json_file(json_data, json_path)
            print(f"\nSaved updated JSON to {json_path}")
        elif logger.verbose:
            print(" No changes detected; skipping write.")
        logger.print_report()
    else:
        if logger.verbose:
            print(" [DRY-RUN] Skipping write.")
        logger.print_report()

    if logger.verbose:
        logger.print_stats_summary()

    return True


def main():
    """Main function to process KV IDs."""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = "./tests/data/source-description.json"

    ##### fill in (e.g., 'op25', 'm317'):
    complex_id = "op25"

    try:
        logger = Logger(dry_run=False, verbose=True)
        success = unify_kv_ids(json_path, complex_id, logger)
        if success:
            print("\n Finished!")
        else:
            print("\n Processing completed with warnings.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except (ValueError, KeyError, OSError, PermissionError) as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
