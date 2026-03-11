#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify Link Box IDs - Pure Python Script

This script unifies link box svgGroupIds in JSON textcritic files
and corresponding SVG files.

For each linkBox:
- The new ID is formatted as: g-lb-{entry_id}-to-{sheetId}
  where sheetId is extracted from the linkTo.sheetId field

Example:
- Entry ID: "M34_Sk1"
- LinkBox svgGroupId: "g6407"
- LinkBox linkTo.sheetId: "M_317_Sk2"
- New ID: "g-lb-m34_sk1c-to-m317_sk2a"
"""

import sys

from utils.extraction_utils import (
        extract_id_suffix,
        extract_moldenhauer_number,
        extract_link_boxes
    )
from utils.file_utils import (
    load_and_validate_inputs, create_svg_loader, save_results
)
from utils.svg_utils import (
    find_matching_svg_files_by_class, find_relevant_svg_files, update_svg_id_by_class
)


# Helper function to append structured messages
def log_report_message(message_list, type_, code, textcritics_entry_id, message):
    """Helper function to log structured messages with consistent formatting.

    Args:
        message_list (list): List to append the message to
        type_ (str): Type of message ("error", "warning", "info")
        code (str): Unique code for the message type
        textcritics_entry_id (str): ID of the textcritics entry for context
        message (str): The message text to log
    """


    msg = f" [{type_.upper()}] {textcritics_entry_id}: {message} [{code}]"
    if message_list is not None:
        message_list.append(msg)
    print(msg)


def process_single_link_box(svg_group_id, parent_link_boxes, textcritics_entry_id, relevant_svgs, get_svg_data, linkbox_prefix, messages=None):
    """Process a single linkBox through the complete update workflow.

    Handles duplicate detection, JSON updates, and SVG file modifications
    for a single link box svgGroupId.

    Args:
        svg_group_id (str): The original ID to replace
        parent_link_boxes (list): List of all linkBoxes in the entry
        textcritics_entry_id (str): The textcritics entry ID for naming
        relevant_svgs (list): List of relevant SVG files for this entry
        get_svg_data (function): Function to load SVG data
        linkbox_prefix (str): Prefix to use for new link box IDs
        messages (list, optional): List to append structured log messages

    Returns:
        bool: True if updated successfully, False if skipped
    """
    linkbox_class = "link-box"

    # Find all matching SVG files for this ID
    matching_files = find_matching_svg_files_by_class(
        svg_group_id, relevant_svgs, get_svg_data, linkbox_class
    )

    if len(matching_files) == 0:
        log_report_message(
            messages, "error", "svg_group_id_not_found", textcritics_entry_id,
            f"'{svg_group_id}' with class '{linkbox_class}' not found in any relevant SVG files"
        )
        return False

    # Find the link box to update by svg_group_id
    link_box = next((lb for lb in parent_link_boxes if lb.get('svgGroupId') == svg_group_id), None)

    # Get target sheetId from linkBox
    target_sheet_id = link_box.get('linkTo', {}).get('sheetId', '')
    if not target_sheet_id:
        log_report_message(
            messages, "error", "missing_sheetid", textcritics_entry_id,
            f"No target sheetId found in linkBox with svgGroupId '{svg_group_id}'"
        )
        return False


    # Log if multiple SVGs reference the same original svgGroupId
    expanded_json = False
    if len(matching_files) > 1:
        print(f" [!] MULTIPLE SVGs reference '{svg_group_id}'. Expanding JSON entry to {len(matching_files)} distinct IDs.")
        expanded_json = True

    # Remove the original linkBox from the parent list
    parent_link_boxes.remove(link_box)

    success = True
    for svg_filename in matching_files:
        # Extract suffix from filename if present
        suffix = extract_id_suffix(svg_filename)
        entry_id = textcritics_entry_id + suffix if suffix else textcritics_entry_id

        # Warn if entry_id is identical to target_sheet_id
        if entry_id == target_sheet_id:
            log_report_message(
                messages, "warning", "self_reference", textcritics_entry_id,
                f"Self-reference detected: entry_id ('{entry_id}') is identical to target_sheet_id ('{target_sheet_id}') for svgGroupId '{svg_group_id}'"
            )

        # Create new ID
        new_group_id = f"{linkbox_prefix}{entry_id}-to-{target_sheet_id}".lower()

        # Duplicate linkBox and update ID in JSON
        new_link_box = dict(link_box)
        new_link_box['svgGroupId'] = new_group_id
        parent_link_boxes.append(new_link_box)

        if expanded_json:
            log_report_message(
                messages, "info", "json_expanded", textcritics_entry_id,
                f"Expanded JSON entry: Added new linkBox with svgGroupId '{new_group_id}' for original '{svg_group_id}'"
                )
        print(f" [JSON] Changing '{svg_group_id}' -> '{new_group_id}'")

        # Update SVG file
        svg_data = get_svg_data(svg_filename)
        svg_data["content"], error = update_svg_id_by_class(
            svg_data["content"], svg_group_id, new_group_id, linkbox_class
        )
        if error:
            print(f" [!] WARNING: {error} in {svg_filename}")
            success = False
        else:
            print(f" [SVG]  Changing '{svg_group_id}' -> '{new_group_id}' in {svg_filename}")

    return success


def process_textcritics_entry(textcritics_entry, all_svg_files, get_svg_data, linkbox_prefix, messages=None):
    """Process a single textcritics entry and all its linkBoxes.

    Args:
        textcritics_entry (dict): Single textcritics entry
        all_svg_files (list): List of all available SVG files
        get_svg_data (function): Function to load SVG data
        linkbox_prefix (str): Prefix to use for new link box IDs
        messages (list, optional): List to append structured log messages

    Returns:
        None: Modifies entry in place and handles file operations
    """
    if not isinstance(textcritics_entry, dict):
        return

    textcritics_entry_id = textcritics_entry.get('id', '')
    if not textcritics_entry_id:
        return

    print(f"\nProcessing textcritics entry ID: {textcritics_entry_id}")

    # Extract all linkBoxes from this entry
    link_boxes = extract_link_boxes(textcritics_entry)

    if not link_boxes:
        print(" No linkBoxes to process")
        return

    print(f" Found {len(link_boxes)} linkBox(es)")

    # Get relevant SVG files for this entry
    current_main_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_main_number
    )

    if "SkRT" in textcritics_entry_id:
        print(f" SkRT anchor detected: {textcritics_entry_id}")
    else:
        print(f" Standard anchor: {textcritics_entry_id}")

    print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    # Iterate over a copy to avoid modifying the list during iteration
    for link_box in list(link_boxes):
        svg_group_id = link_box.get('svgGroupId', '')
        if not svg_group_id:
            log_report_message(messages, "error", "missing_svgGroupId", textcritics_entry_id, "linkBox without svgGroupId")
            continue

        process_single_link_box(
            svg_group_id, link_boxes, textcritics_entry_id,
            relevant_svgs, get_svg_data, linkbox_prefix, messages
        )

    # Sort linkBoxes by svgGroupId after all processing
    if isinstance(link_boxes, list):
        link_boxes.sort(key=lambda lb: lb.get('svgGroupId', ''))


def unify_link_box_ids(json_path, svg_folder, linkbox_prefix="g-lb-"):
    """Unify link box IDs in JSON and SVG files.

    For each JSON entry:
    1. Collect all linkBoxes
    2. Find those IDs in relevant SVG files (with link-box class)
    3. Replace with {entry_id}to{sheetId} format

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files
        linkbox_prefix (str): Prefix to use for new link box IDs (default: "g-lb-")

    Returns:
        bool: True if processing completed successfully
    """
    print("--- Starting Link Box ID processing ---")

    # Load and validate inputs
    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    # Initialize SVG loader
    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_data = create_svg_loader(
        svg_folder, final_svg_cache, loaded_svg_texts
    )

    # Get entries from textcritics data structure
    all_textcritics_entries = (
        json_data.get('textcritics', json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    # Collect all report messages across entries
    report_messages = []

    # Process each textcritics entry independently
    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry, all_svg_files, get_svg_data, linkbox_prefix, report_messages
        )

    # Save all modified files
    save_results(json_data, loaded_svg_texts, json_path)

    print("\n--- Link Box ID processing completed ---")

    # TODO: Validation that there is no link-box class in relevant svgs
    # that do not have a corresponding entry in textcritics.json

    if report_messages:
        print("\n--- REPORT ---")
        error_warning_msgs = [msg for msg in report_messages if msg.startswith(" [ERROR]") or msg.startswith(" [WARNING]")]
        info_msgs = [msg for msg in report_messages if msg.startswith(" [INFO]")]
        if error_warning_msgs:
            print("\n--- Errors and Warnings ---")
            for msg in error_warning_msgs:
                print(msg)
        if info_msgs:
            print("\n--- Info Messages ---")
            for msg in info_msgs:
                print(msg)
    else:
        print("\n [✓] All JSON and SVG 'linkbox' IDs successfully updated.")

    return True


def main():
    """Main function to process link box IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/'

    linkbox_prefix = "g-lb-"  # TODO: move to awg-lb

    try:
        success = unify_link_box_ids(json_path, svg_folder, linkbox_prefix)
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
