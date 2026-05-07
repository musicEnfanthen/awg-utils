#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Utils Module for TKK ID Unification

This module contains all file operation functions for loading, validating,
and saving JSON and SVG files during the TKK ID unification process.
"""

import json
import os
import re
import xml.etree.ElementTree as ET


def load_and_validate_inputs(json_path, svg_folder):
    """Load and validate input files and directories.

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files

    Returns:
        tuple: (data, all_svg_files) - loaded JSON data and list of SVG files

    Raises:
        FileNotFoundError: If the JSON file or SVG folder does not exist.
        json.JSONDecodeError: If the JSON file contains malformed JSON.
        PermissionError: If the SVG folder cannot be listed.
        ValueError: If no SVG files are found in the folder.
    """
    data = load_json_file(json_path)
    all_svg_files = _load_svg_files(svg_folder)

    entry_count = (
        len(data.get("textcritics", [])) if isinstance(data, dict) else "nested"
    )
    print(f"Loaded JSON with {entry_count} textcritics entries")
    print(f"Found {len(all_svg_files)} SVG files in folder")

    return data, all_svg_files


def load_json_file(json_path):
    """Load and return JSON data from a file.

    Args:
        json_path (str): Path to the JSON file.

    Returns:
        dict | list: Parsed JSON data.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_svg_files(svg_folder):
    """List and validate SVG files in a folder.

    Args:
        svg_folder (str): Path to the folder containing SVG files.

    Returns:
        list[str]: Filenames of all SVG files found (case-insensitive).

    Raises:
        FileNotFoundError: If the folder does not exist.
        PermissionError: If the folder cannot be listed.
        ValueError: If no SVG files are found in the folder.
    """
    if not os.path.exists(svg_folder):
        raise FileNotFoundError(f"SVG folder not found: {svg_folder}")
    try:
        all_files = os.listdir(svg_folder)
        all_svg_files = [f for f in all_files if f.lower().endswith(".svg")]
    except OSError as e:
        raise PermissionError(
            f"Cannot list contents of SVG folder: {svg_folder} - {e}"
        ) from e
    if not all_svg_files:
        raise ValueError(f"No SVG files found in folder: {svg_folder}")
    return all_svg_files


def create_svg_loader(svg_folder, svg_file_cache):
    """Create a closure function for loading SVG files with caching.

    Args:
        svg_folder (str): Path to the folder containing SVG files
        svg_file_cache (dict): Cache for currently loaded SVG files

    Returns:
        function: A function that loads and caches SVG content
    """

    def get_svg_data(filename):
        if filename not in svg_file_cache:
            path = os.path.join(svg_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            has_xml_declaration = bool(re.match(r"^\s*<\?xml\b", content))
            svg_root, _ = _parse_svg_xml(content)
            svg_file_cache[filename] = {
                "svg_root": svg_root,
                "path": path,
                "has_xml_declaration": has_xml_declaration,
                "dirty": False,
            }
        return svg_file_cache[filename]

    return get_svg_data


def save_json_file(data, json_path):
    """Save JSON data to file with proper formatting.

    Args:
        data (dict): JSON data to save
        json_path (str): Path to save the JSON file

    Returns:
        None: Saves file directly to disk
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def save_results(data, svg_file_cache, json_path):
    """Save all modified files.

    Args:
        data (dict): Modified JSON data to save
        svg_file_cache (dict): Cache for currently loaded SVG files to save
        json_path (str): Path to save the JSON file

    Returns:
        None: Saves files
    """
    # Final save of any remaining SVG files
    _save_svg_files(svg_file_cache)

    # Save updated JSON
    save_json_file(data, json_path)


def _parse_svg_xml(svg_content):
    """Parse SVG XML content into an ElementTree root.

    Args:
        svg_content (str): The SVG content to parse

    Returns:
        tuple: (root_element_or_none, error_message_or_none)
    """
    try:
        return ET.fromstring(svg_content), None
    except ET.ParseError as e:
        return None, f"XML parse error: {e}"


def _save_svg_files(loaded_svg_texts):
    """Save all dirty SVG files to disk by serializing their parsed trees.

    Args:
        loaded_svg_texts (dict): Dictionary of loaded SVG data with svg_root and paths

    Returns:
        None: Saves files directly to disk
    """
    for _, sdata in loaded_svg_texts.items():
        if not sdata.get("dirty", False):
            continue
        content = _serialize_svg_xml(
            sdata["svg_root"],
            include_xml_declaration=sdata.get("has_xml_declaration", True),
        )
        with open(sdata["path"], "w", encoding="utf-8") as f:
            f.write(content)


def _serialize_svg_xml(parsed_svg_root, include_xml_declaration=True):
    """Serialize SVG ElementTree root with stable declaration and EOF newline.

    Args:
        parsed_svg_root (Element): The root element of the parsed SVG.
        include_xml_declaration (bool): Whether to include XML declaration.

    Returns:
        str: Serialized SVG content.
    """
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    updated_content = ET.tostring(
        parsed_svg_root, encoding="unicode", xml_declaration=include_xml_declaration
    )

    # Normalize XML declaration:
    if updated_content.startswith("<?xml"):
        decl_end = updated_content.find("?>") + 2
        xml_decl = updated_content[:decl_end]
        rest = updated_content[decl_end:]
        xml_decl = xml_decl.replace("'", '"')
        xml_decl = xml_decl.replace("utf-8", "UTF-8")
        updated_content = xml_decl + rest

    # Remove whitespace before self-closing tags
    updated_content = re.sub(r"\s+/>", "/>", updated_content)

    # Add newline at the end if not present
    if not updated_content.endswith("\n"):
        updated_content += "\n"

    return updated_content
