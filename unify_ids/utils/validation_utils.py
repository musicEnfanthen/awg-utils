#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation utilities for TKK ID processing.

This module contains functions for validating the success of TKK ID unification
across JSON and SVG files, ensuring all IDs have been properly updated.
"""

import re

from .extraction_utils import has_class_token

def validate_json_entries(data, prefix):
    """Validate JSON entries for unchanged svgGroupId values.

    Args:
        data (dict): The processed JSON textcritics data structure
        prefix (str): The target prefix that all updated IDs should start with

    Returns:
        int: Number of errors found
    """
    errors_found = 0
    all_entries = data.get('textcritics', data) if isinstance(data, dict) else data

    for entry in all_entries:
        entry_id = entry.get('id', 'Unknown')
        comments_list = entry.get('commentary', {}).get('comments', [])
        for comment_group in comments_list:
            for block_comment in comment_group.get('blockComments', []):
                val = block_comment.get('svgGroupId')
                if val and not val.startswith(prefix) and val != "TODO":
                    print(f"  [!] JSON ERROR: Unchanged ID '{val}' in Entry: {entry_id}")
                    errors_found += 1

    return errors_found


_G_TAG_RE = re.compile(r"<g\b[^>]*>", re.IGNORECASE | re.DOTALL)
_ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*(\"[^\"]*\"|'[^']*')", re.DOTALL)


def _extract_attrs(tag_text):
    """
    Extracts attribute key-value pairs from an SVG tag string.

    Args:
        tag_text (str): The SVG tag text to parse.

    Returns:
        dict: Dictionary of attribute names (lowercased) mapped to their values (unquoted).
    """
    attrs = {}
    for name, quoted in _ATTR_RE.findall(tag_text):
        attrs[name.lower()] = quoted[1:-1]
    return attrs



def validate_svg_entries(loaded_svgs, id_prefix, required_class="tkk"):
    """
    Validate SVG entries for IDs that have not been updated with the required prefix.

    Args:
        loaded_svgs (dict): Dictionary mapping SVG filenames to their content and metadata.
        id_prefix (str): The target prefix that all updated SVG IDs should start with.
        required_class (str): The required class name for SVG elements to be validated
                            (default is "tkk").

    Returns:
        int: Number of SVG ID errors found (IDs not updated with the prefix).
    """
    errors = 0
    for svg_filename, svg_data in loaded_svgs.items():
        content = (svg_data or {}).get("content", "")
        seen = set()

        for g_tag in _G_TAG_RE.findall(content):
            attrs = _extract_attrs(g_tag)
            svg_id = attrs.get("id")
            class_attr = attrs.get("class", "")

            if not svg_id or svg_id in seen:
                continue
            if not has_class_token(class_attr, required_class):
                continue

            seen.add(svg_id)
            if not svg_id.startswith(id_prefix):
                errors += 1
                print(
                    f"  [!] SVG ORPHAN: ID '{svg_id}' with class '{required_class}' "
                    f"in {svg_filename} was NOT updated."
                )

    return errors


def display_validation_report(data, id_prefix, loaded_svgs, required_class="tkk"):
    """Validate and report the success of TKK ID unification process.

    Performs post-processing validation to ensure all TKK-related IDs have been
    properly updated with the specified prefix. Identifies and reports:
    - JSON entries with unchanged svgGroupId values (excluding "TODO" entries)
    - SVG elements with class="tkk" that retain old ID values

    Generates a comprehensive error report with specific file locations and
    entry IDs for debugging purposes.

    Args:
        data (dict): The processed JSON textcritics data structure containing
                    textcritics entries with commentary and blockComments.
        id_prefix (str): The target prefix that all updated IDs should start with
                     (e.g., "awg-tkk-").
        loaded_svgs (dict): Dictionary mapping SVG filenames to their content
                           and path information from the processing cache.
        required_class (str): The required class name for SVG elements to be
                            validated (default is "tkk").

    Returns:
        None: Prints validation results directly to stdout. Does not return values.
    """
    print("\n--- UNCERTAINTY & ERROR REPORT ---")

    json_errors = validate_json_entries(data, id_prefix)
    svg_errors = validate_svg_entries(
        loaded_svgs, id_prefix, required_class=required_class
    )
    total_errors = json_errors + svg_errors

    if total_errors == 0:
        print("  [✓] All JSON and SVG 'tkk' IDs successfully updated.")
    else:
        print(f"  [!] Total issues found: {total_errors}")
