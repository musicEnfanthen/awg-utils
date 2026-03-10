#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Utils Module for TKK ID Unification

This module contains all file operation functions for loading, validating,
and saving JSON and SVG files during the TKK ID unification process.
"""

import json
import os


def load_and_validate_inputs(json_path, svg_folder):
    """Load and validate input files and directories.

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files

    Returns:
        tuple: (data, all_svg_files) - loaded JSON data and list of SVG files

    Raises:
        FileNotFoundError: If JSON file or SVG folder doesn't exist
    """
    # Check if paths exist
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    if not os.path.exists(svg_folder):
        raise FileNotFoundError(f"SVG folder not found: {svg_folder}")

    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get SVG files and validate folder content
    try:
        all_files = os.listdir(svg_folder)
        all_svg_files = [f for f in all_files if f.lower().endswith('.svg')]
    except OSError as e:
        raise PermissionError(f"Cannot list contents of SVG folder: {svg_folder} - {e}") from e

    if not all_svg_files:
        raise ValueError(f"No SVG files found in folder: {svg_folder}")

    entry_count = len(data.get('textcritics', [])) if isinstance(data, dict) else 'nested'
    print(f"Loaded JSON with {entry_count} textcritics entries")
    print(f"Found {len(all_svg_files)} SVG files in folder")

    return data, all_svg_files


def create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts):
    """Create a closure function for loading SVG files with caching.

    Args:
        svg_folder (str): Path to the folder containing SVG files
        final_svg_cache (dict): Cache for final SVG results
        loaded_svg_texts (dict): Cache for currently loaded SVG texts

    Returns:
        function: A function that loads and caches SVG content
    """
    def get_svg_text(filename):
        if filename not in loaded_svg_texts:
            path = os.path.join(svg_folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            loaded_svg_texts[filename] = {"content": content, "path": path}
            final_svg_cache[filename] = loaded_svg_texts[filename]
        return loaded_svg_texts[filename]
    return get_svg_text


def save_svg_files(loaded_svg_texts):
    """Save all currently loaded SVG files to disk.

    Args:
        loaded_svg_texts (dict): Dictionary of loaded SVG data with content and paths

    Returns:
        None: Saves files directly to disk
    """
    for _, sdata in loaded_svg_texts.items():
        with open(sdata['path'], 'w', encoding='utf-8') as f:
            f.write(sdata['content'])


def save_json_file(data, json_path):
    """Save JSON data to file with proper formatting.

    Args:
        data (dict): JSON data to save
        json_path (str): Path to save the JSON file

    Returns:
        None: Saves file directly to disk
    """
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')  # Add trailing newline


def save_results(data, loaded_svg_texts, json_path):
    """Save all modified files.

    Args:
        data (dict): Modified JSON data to save
        loaded_svg_texts (dict): Currently loaded SVG texts to save
        json_path (str): Path to save the JSON file

    Returns:
        None: Saves files
    """
    # Final save of any remaining SVG files
    save_svg_files(loaded_svg_texts)

    # Save updated JSON
    save_json_file(data, json_path)
