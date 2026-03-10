#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extraction Utilities for TKK ID Processing

This module provides utility functions for extracting and parsing various
identifiers and data structures used in TKK ID processing workflows.

Functions:
    - extract_id_suffix: Extracts suffix for linkBox IDs from SVG filenames
    - extract_moldenhauer_number: Extracts catalog numbers from entry ID strings
    - extract_svg_group_ids: Extracts svgGroupIds from JSON entry structures
    - extract_link_boxes: Extracts linkBox objects from JSON entry structures

Usage:
    from utils.extraction_utils import (
        extract_id_suffix,
        extract_moldenhauer_number,
        extract_svg_group_ids,
        extract_link_boxes
    )

    suffix = extract_id_suffix("M35_42_Sk1-3von6-final.svg")
    number = extract_moldenhauer_number("M_143_TF1")
    ids, comments = extract_svg_group_ids(entry_data)
    link_boxes = extract_link_boxes(entry_data)
"""

import re

def extract_id_suffix(svg_filename):
    """
    Extract the suffix for a linkBox ID from an SVG filename based on '-NvonM-' pattern.

    Supports filenames containing '-NvonM-' (e.g., '-3von6-', '-9von12-', '-1von1-').
    - For '1von1', returns an empty string (no suffix).
    - For other values, returns a letter suffix (1->'a', 2->'b', ...).
    - If the pattern is not found, returns 'x'.

    Args:
        svg_filename (str): The SVG filename to extract the suffix from.

    Returns:
        str: The extracted suffix for the ID, or 'x' if not found.
    """
    m = re.search(r'-(\d+)von(\d+)-', svg_filename)
    if m:
        num = int(m.group(1))
        total = int(m.group(2))
        if num == 1 and total == 1:
            return ''
        else:
            return chr(ord('a') + num - 1)
    else:
        return 'x'


def extract_moldenhauer_number(text):
    """Extract the Moldenhauer catalog number from entry ID strings.

    Supports both underscore and non-underscore patterns:
    - 'M_143_TF1' -> '143' (classic format with underscore)
    - 'M143_Textfassung1' -> '143' (filename format without underscore)
    - 'Mx_136_Sk1' -> '136' (Mx variant with underscore)
    - 'Mx789_file' -> '789' (Mx variant without underscore)

    Args:
        text (str): The entry ID or filename to extract number from.
                   None values are converted to string automatically.

    Returns:
        str: The extracted Moldenhauer number as string, or empty string if no match found.
    """
    match = re.search(r'Mx?_?(\d+)', str(text))
    return match.group(1) if match else ""


def extract_svg_group_ids(entry):
    """Extract all svgGroupIds and their corresponding block comments from an entry.

    Args:
        entry (dict): Single textcritics entry

    Returns:
        tuple: (svg_group_ids, block_comments) - lists of IDs and their comment objects
    """
    svg_group_ids = []
    block_comments = []

    comments_list = entry.get('commentary', {}).get('comments', [])
    for comment_group in comments_list:
        for block_comment in comment_group.get('blockComments', []):
            svg_group_id = block_comment.get('svgGroupId')
            if svg_group_id and svg_group_id != "TODO":
                svg_group_ids.append(svg_group_id)
                block_comments.append(block_comment)

    return svg_group_ids, block_comments

def extract_link_boxes(entry):
    """Extract all linkBoxes from an entry.

    Args:
        entry (dict): Single textcritics entry

    Returns:
        list: List of linkBox objects with svgGroupId and linkTo information
    """
    link_boxes = entry.get('linkBoxes', [])
    return link_boxes if isinstance(link_boxes, list) else []
