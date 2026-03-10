#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG utilities for TKK Group ID processing

Functions for finding, matching, and updating SVG files and their content.
"""

import re
from .extraction_utils import extract_moldenhauer_number


def find_matching_svg_files(svg_group_id, relevant_svgs, get_svg_data):
    """Find all SVG files that contain a specific svgGroupId with tkk class.

    Args:
        svg_group_id (str): The ID to search for
        relevant_svgs (list): List of relevant SVG filenames to search in
        get_svg_data (function): Function to load SVG data

    Returns:
        list: List of SVG filenames that contain the ID with tkk class
    """
    matching_files = []
    for svg_filename in relevant_svgs:
        svg_data = get_svg_data(svg_filename)
        # Test if this ID exists with class tkk in this SVG
        test_content, error = update_svg_id(svg_data["content"], svg_group_id, "test")
        if error is None and test_content != svg_data["content"]:
            matching_files.append(svg_filename)
    return matching_files


def find_relevant_svg_files(new_id, all_svg_files, current_main_number):
    """Find relevant SVG files for a given entry ID.

    Args:
        new_id (str): The entry ID
        all_svg_files (list): List of all SVG files
        current_main_number (str): Extracted number from the ID

    Returns:
        list: List of relevant SVG filenames
    """
    # Helper function for candidate filtering
    def matches_moldenhauer_number(filename):
        return current_main_number == extract_moldenhauer_number(filename)

    # SkRT entries: only row table files
    if "SkRT" in new_id:
        return [
            f for f in all_svg_files
            if matches_moldenhauer_number(f) and "Reihentabelle" in f
        ]

    # Filter candidate files: matching Moldenhauer number, excluding row table files
    candidate_svg_files = [
        f for f in all_svg_files
        if matches_moldenhauer_number(f) and "Reihentabelle" not in f
    ]

    # TF entries: specific Textfassung
    tf_match = re.search(r'TF(\d+)', new_id)
    if tf_match:
        tf_number = tf_match.group(1)
        return [f for f in candidate_svg_files if f"Textfassung{tf_number}" in f]

    # Sk entries: specific Sketch with exact matching
    sk_match = re.search(r'(Sk\d+(?:_\d+)*)', new_id)
    if sk_match:
        sk_identifier = sk_match.group(1)
        # Prevent matching when the Sk identifier is followed by any digit or underscore
        pattern = rf'{re.escape(sk_identifier)}(?![\d_])'
        return [f for f in candidate_svg_files if re.search(pattern, f)]

    # Default: all non-Reihentabelle files for this Moldenhauer number
    return candidate_svg_files


def update_svg_id(svg_content, old_val, new_val):
    """Update an ID in SVG content while preserving elements with class="tkk".

    Handles elements that may have multiple CSS classes, as long as "tkk" is one of them.
    Supports both single and double quotes, and various attribute orders.

    Examples of supported formats:
    - <g class="tkk" id="old-id">  (single class)
    - <g class="tkk other-class" id="old-id">  (tkk first)
    - <g class="active tkk selected" id="old-id">  (tkk in middle)
    - <g id="old-id" class='other-class tkk'>  (tkk last, single quotes)

    Args:
        svg_content (str): The SVG content to process
        old_val (str): The old ID value to replace
        new_val (str): The new ID value to use as replacement

    Returns:
        tuple: (updated_content, error_message)
               error_message is None if successful, string if error occurred
    """
    # Only match the ID if the same tag contains class with "tkk" as a word
    escaped_id = re.escape(old_val)

    # Create patterns for both quote styles and both attribute orders
    # Use word boundaries (\b) to match "tkk" as complete word within class attribute
    patterns = [
        # Double quotes: id first, then class with tkk
        f'<[^>]*?id="{escaped_id}"[^>]*?class="[^"]*\\btkk\\b[^"]*"[^>]*?>',
        # Double quotes: class with tkk first, then id
        f'<[^>]*?class="[^"]*\\btkk\\b[^"]*"[^>]*?id="{escaped_id}"[^>]*?>',
        # Single quotes: id first, then class with tkk
        f"<[^>]*?id='{escaped_id}'[^>]*?class='[^']*\\btkk\\b[^']*'[^>]*?>",
        # Single quotes: class with tkk first, then id
        f"<[^>]*?class='[^']*\\btkk\\b[^']*'[^>]*?id='{escaped_id}'[^>]*?>",
    ]

    # Count total tkk matches first
    total_tkk_matches = 0
    for pattern in patterns:
        total_tkk_matches += len(re.findall(pattern, svg_content))

    if total_tkk_matches > 1:
        return (svg_content,
                f"Multiple class='tkk' elements found with ID '{old_val}' "
                f"({total_tkk_matches} occurrences)")

    def replace_id(match):
        full_tag = match.group(0)
        return (full_tag.replace(f'id="{old_val}"', f'id="{new_val}"')
                        .replace(f"id='{old_val}'", f"id='{new_val}'"))

    # Apply all patterns
    content = svg_content
    for pattern in patterns:
        content = re.sub(pattern, replace_id, content)
    return content, None

def update_svg_id_by_class(svg_content, old_val, new_val, target_class):
    """Update an ID in SVG content for elements with a specific class.

    Similar to update_svg_id but allows specifying which class to match.
    Supports both single and double quotes, and various attribute orders.

    Args:
        svg_content (str): The SVG content to process
        old_val (str): The old ID value to replace
        new_val (str): The new ID value to use as replacement
        target_class (str): The CSS class to match (e.g., "link-box", "tkk")

    Returns:
        tuple: (updated_content, error_message)
               error_message is None if successful, string if error occurred
    """
    escaped_id = re.escape(old_val)
    escaped_class = re.escape(target_class)

    # Create patterns for both quote styles and both attribute orders
    # Use word boundaries (\b) to match the class as complete word within class attribute
    patterns = [
        # Double quotes: id first, then class with target class
        f'<[^>]*?id="{escaped_id}"[^>]*?class="[^"]*\\b{escaped_class}\\b[^"]*"[^>]*?>',
        # Double quotes: class with target class first, then id
        f'<[^>]*?class="[^"]*\\b{escaped_class}\\b[^"]*"[^>]*?id="{escaped_id}"[^>]*?>',
        # Single quotes: id first, then class with target class
        f"<[^>]*?id='{escaped_id}'[^>]*?class='[^']*\\b{escaped_class}\\b[^']*'[^>]*?>",
        # Single quotes: class with target class first, then id
        f"<[^>]*?class='[^']*\\b{escaped_class}\\b[^']*'[^>]*?id='{escaped_id}'[^>]*?>",
    ]

    # Count total matches first
    total_matches = 0
    for pattern in patterns:
        total_matches += len(re.findall(pattern, svg_content))

    if total_matches > 1:
        return (svg_content,
                f"Multiple class='{target_class}' elements found with ID '{old_val}' "
                f"({total_matches} occurrences)")

    def replace_id(match):
        full_tag = match.group(0)
        return (full_tag.replace(f'id="{old_val}"', f'id="{new_val}"')
                        .replace(f"id='{old_val}'", f"id='{new_val}'"))

    # Apply all patterns
    content = svg_content
    for pattern in patterns:
        content = re.sub(pattern, replace_id, content)
    return content, None


def _extract_attr(tag_text: str, attr_name: str):
    m = re.search(
        rf"""\b{re.escape(attr_name)}\s*=\s*(['"])(.*?)\1""",
        tag_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return m.group(2) if m else ""

def _has_class_token(class_attr: str, wanted_class: str) -> bool:
    wanted = (wanted_class or "").strip().lower()
    if not wanted:
        return False
    return any(token.lower() == wanted for token in class_attr.split())

def find_matching_svg_files_by_class(svg_group_id, relevant_svg_files, get_svg_data, required_class="tkk"):
    matching = []
    tag_re = re.compile(
        rf"""<[A-Za-z_:][\w:.-]*[^>]*\bid\s*=\s*(['"]){re.escape(svg_group_id)}\1[^>]*>""",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for svg_filename in relevant_svg_files:
        svg_data = get_svg_data(svg_filename)
        if not svg_data:
            continue
        content = svg_data.get("content", "")
        for tag_match in tag_re.finditer(content):
            class_attr = _extract_attr(tag_match.group(0), "class")
            if _has_class_token(class_attr, required_class):
                matching.append(svg_filename)
                break

    return matching

def update_svg_id_by_class(svg_content, old_id, new_id, required_class="tkk"):
    replaced = False
    tag_re = re.compile(
        rf"""<[A-Za-z_:][\w:.-]*[^>]*\bid\s*=\s*(['"]){re.escape(old_id)}\1[^>]*>""",
        flags=re.IGNORECASE | re.DOTALL,
    )
    id_attr_re = re.compile(
        rf"""(\bid\s*=\s*)(['"]){re.escape(old_id)}\2""",
        flags=re.IGNORECASE,
    )

    def _replace_tag(match):
        nonlocal replaced
        tag = match.group(0)
        if replaced:
            return tag

        class_attr = _extract_attr(tag, "class")
        if not _has_class_token(class_attr, required_class):
            return tag

        replaced = True
        return id_attr_re.sub(
            lambda m: f"{m.group(1)}{m.group(2)}{new_id}{m.group(2)}",
            tag,
            count=1,
        )

    updated_content = tag_re.sub(_replace_tag, svg_content)

    if not replaced:
        return svg_content, f"'{old_id}' with class containing '{required_class}' not found"

    return updated_content, None
