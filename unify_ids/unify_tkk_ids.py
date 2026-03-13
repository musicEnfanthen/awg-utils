#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify TKK Group IDs - Pure Python Script
Made by Eli (lili041 --Github) with Google Gemini
"""

import re
import sys
from utils.extraction_utils import (
    extract_moldenhauer_number, extract_svg_group_ids
)
from utils.file_utils import (
    load_and_validate_inputs, create_svg_loader, save_results
)
from utils.svg_utils import (
    find_matching_svg_files, find_relevant_svg_files, update_svg_id
)
from utils.validation_utils import display_validation_report

_G_TAG_RE = re.compile(r"<g\b[^>]*>", re.IGNORECASE | re.DOTALL)
_ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*(\"[^\"]*\"|'[^']*')", re.DOTALL)


def _init_stats():
    return {
        "entries_seen": 0,
        "ids_seen": 0,
        "ids_changed": 0,
        "ids_missing": 0,
        "ids_multiple": 0,
        "svg_noop": 0,
    }


def _bump(stats, key, amount=1):
    if stats is not None:
        stats[key] = stats.get(key, 0) + amount


def _extract_attrs(tag_text):
    attrs = {}
    for name, value in _ATTR_RE.findall(tag_text):
        attrs[name.lower()] = value[1:-1]
    return attrs


def _class_contains(class_attr, needle="tkk"):
    return (needle or "").strip().lower() in (class_attr or "").lower()


def _coerce_update_result(update_result, original_content):
    """
    Normalize update_svg_id() return variants:
    - updated_content
    - (updated_content, changed_bool)
    - (updated_content, error_message_or_none)
    """
    updated_content = original_content
    changed = False
    update_error = None

    if isinstance(update_result, tuple):
        if len(update_result) >= 1:
            updated_content = update_result[0]
        if len(update_result) >= 2:
            second = update_result[1]
            if isinstance(second, bool):
                changed = second
            else:
                # legacy style: None => success, str => error
                update_error = second
                changed = second is None
        else:
            changed = updated_content != original_content
    else:
        updated_content = update_result
        changed = updated_content != original_content

    return updated_content, changed, update_error


def _build_tkk_id_index(relevant_svgs, get_svg_data):
    """Build map: svgGroupId -> [svg filenames], scanning each SVG once."""
    id_to_files = {}

    for svg_filename in relevant_svgs:
        svg_data = get_svg_data(svg_filename)
        content = svg_data.get("content", "")
        seen_ids_in_file = set()

        for g_tag in _G_TAG_RE.findall(content):
            attrs = _extract_attrs(g_tag)
            svg_id = attrs.get("id")
            class_attr = attrs.get("class", "")

            # class only needs to contain "tkk"
            if svg_id and _class_contains(class_attr, "tkk") and svg_id not in seen_ids_in_file:
                id_to_files.setdefault(svg_id, []).append(svg_filename)
                seen_ids_in_file.add(svg_id)

    return id_to_files


def _get_cached_matching_files(svg_group_id, relevant_svgs, get_svg_data, cache):
    """Fallback cache using existing matching logic."""
    if svg_group_id not in cache:
        cache[svg_group_id] = find_matching_svg_files(
            svg_group_id, relevant_svgs, get_svg_data
        )
    return cache[svg_group_id]


def process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                                get_svg_data, new_id, dry_run=False,
                                stats=None, verbose=True,
                                require_svg_change=False):
    """Process a single svgGroupId through the complete update workflow."""
    if len(matching_files) == 0:
        _bump(stats, "ids_missing")
        if verbose:
            print(
                f" [!] ERROR: '{svg_group_id}' with class 'tkk' not found "
                f"in any relevant SVG files"
            )
        return False

    if len(matching_files) > 1:
        _bump(stats, "ids_multiple")
        if verbose:
            print(
                f" [!] WARNING: '{svg_group_id}' found in {len(matching_files)} "
                f"files: {matching_files}"
            )
            print(
                "     Skipping due to multiple occurrences - "
                "manual review required"
            )
        return False

    svg_filename = matching_files[0]
    svg_data = get_svg_data(svg_filename)

    update_result = update_svg_id(svg_data["content"], svg_group_id, new_id)
    updated_content, changed, update_error = _coerce_update_result(
        update_result, svg_data["content"]
    )

    if require_svg_change and not changed:
        _bump(stats, "svg_noop")
        if verbose:
            if update_error:
                print(
                    f" [!] WARNING: Could not update '{svg_group_id}' in "
                    f"{svg_filename}; JSON unchanged ({update_error})"
                )
            else:
                print(
                    f" [!] WARNING: Could not update '{svg_group_id}' in "
                    f"{svg_filename}; JSON unchanged"
                )
        return False

    _bump(stats, "ids_changed")

    if verbose:
        dry_marker = " [DRY-RUN]" if dry_run else ""
        print(f"{dry_marker} [JSON] Changing '{svg_group_id}' -> '{new_id}'")
        print(f"{dry_marker} [SVG]  Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}")

    if dry_run:
        return True

    # Keep old behavior for direct unit tests
    block_comment['svgGroupId'] = new_id
    svg_data["content"] = updated_content
    return True


def process_textcritics_entry(
        textcritics_entry, all_svg_files, get_svg_data, tkk_prefix,
        dry_run=False, stats=None, verbose=True, use_index=False):
    """Process a single textcritics entry and all its block comments."""
    if not isinstance(textcritics_entry, dict):
        return

    textcritics_entry_id = textcritics_entry.get('id', '')
    if not textcritics_entry_id:
        return

    _bump(stats, "entries_seen")
    if verbose:
        print(f"\nProcessing textcritics entry ID: {textcritics_entry_id}")

    svg_group_ids, block_comments = extract_svg_group_ids(textcritics_entry)

    if not svg_group_ids:
        if verbose:
            print(" No svgGroupIds to process")
        return

    current_main_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_main_number
    )

    if verbose:
        if "SkRT" in textcritics_entry_id:
            print(f" SkRT anchor detected: {textcritics_entry_id}")
        else:
            print(f" Standard anchor: {textcritics_entry_id}")
        print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")



    tkk_id_index = {}
    fallback_cache = {}
    if use_index:
        try:
            tkk_id_index = _build_tkk_id_index(relevant_svgs, get_svg_data)
        except (TypeError, AttributeError, KeyError):
            # Keep tests/mocked flows compatible
            tkk_id_index = {}

    counter = 1
    entry_id_formatted = textcritics_entry_id.lower()

    for svg_group_id, block_comment in zip(svg_group_ids, block_comments):
        _bump(stats, "ids_seen")

        if use_index and svg_group_id in tkk_id_index:
            matching_files = tkk_id_index[svg_group_id]
        else:
            if use_index:
                matching_files = _get_cached_matching_files(
                    svg_group_id, relevant_svgs, get_svg_data, fallback_cache
                )
            else:
                # Old behavior (important for existing tests)
                matching_files = find_matching_svg_files(
                    svg_group_id, relevant_svgs, get_svg_data
                )

        new_id = f"{tkk_prefix}{entry_id_formatted}-{counter:03d}"

        # Keep old call shape when defaults are used (test compatibility)
        if use_index or dry_run or stats is not None or not verbose:
            updated = process_single_svg_group_id(
                svg_group_id, block_comment, matching_files,
                get_svg_data, new_id,
                dry_run=dry_run, stats=stats, verbose=verbose,
                require_svg_change=use_index
            )
        else:
            updated = process_single_svg_group_id(
                svg_group_id, block_comment, matching_files,
                get_svg_data, new_id
            )

        if updated:
            counter += 1


def unify_tkk_ids(json_path, svg_folder, tkk_prefix="awg-tkk-",
                  dry_run=False, verbose=True):
    """Unify TKK IDs in JSON and SVG files."""
    if verbose:
        print("--- Starting TKK ID processing ---")
        if dry_run:
            print(" [DRY-RUN] No files will be written.")

    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_data = create_svg_loader(
        svg_folder, final_svg_cache, loaded_svg_texts
    )

    all_textcritics_entries = (
        json_data.get('textcritics', json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    stats = _init_stats()

    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry, all_svg_files, get_svg_data, tkk_prefix,
            dry_run=dry_run, stats=stats, verbose=verbose, use_index=True
        )

    if not dry_run:
        if stats["ids_changed"] > 0:
            save_results(json_data, loaded_svg_texts, json_path)
        elif verbose:
            print(" No changes detected; skipping writes.")

        display_validation_report(json_data, tkk_prefix, loaded_svg_texts)
    elif verbose:
        print(" [DRY-RUN] Skipping write + validation report.")

    if verbose:
        print(
            " Summary: "
            f"entries={stats['entries_seen']}, "
            f"ids_seen={stats['ids_seen']}, "
            f"changed={stats['ids_changed']}, "
            f"missing={stats['ids_missing']}, "
            f"multiple={stats['ids_multiple']}, "
            f"svg_noop={stats['svg_noop']}"
        )

    return True


def main():
    """Main function to process tkk IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/'

    tkk_prefix = "awg-tkk-"

    try:
        success = unify_tkk_ids(json_path, svg_folder, tkk_prefix)
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
