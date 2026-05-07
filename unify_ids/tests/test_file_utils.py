#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for file_utils.py module

This test suite provides comprehensive testing for the file operation utilities
used in TKK ID processing. The file_utils module handles all file I/O operations
including JSON loading, SVG file caching, and result persistence.

Test Categories:
- load_and_validate_inputs function tests (JSON and SVG directory validation)
- create_svg_loader function tests (SVG file caching and loading mechanics)
- save_results function tests (JSON and SVG file persistence)
- Error handling and edge cases for file operations
- File system interaction and validation scenarios

Usage:
    python -m pytest tests/test_file_utils.py -v
    python -m pytest tests/test_file_utils.py::TestLoadAndValidateInputs -v
    python -m pytest tests/test_file_utils.py::TestCreateSvgLoader -v
"""

import unittest
import json
import os
import tempfile
import shutil
import xml.etree.ElementTree as ET
from unittest.mock import patch
from io import StringIO
import pytest

# Import the functions we want to test
from utils.file_utils import (
    load_and_validate_inputs,
    load_json_file,
    _load_svg_files,
    create_svg_loader,
    save_json_file,
    save_results,
    _parse_svg_xml,
    _serialize_svg_xml,
    _save_svg_files,
)


@pytest.mark.unit
class TestLoadJsonFile(unittest.TestCase):
    """Tests for the load_json_file function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.test_data = {"textcritics": [{"id": "M143_TF1"}]}
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_parsed_data(self):
        """Valid JSON file is loaded and returned as a dict."""
        data = load_json_file(self.json_file)
        self.assertEqual(data, self.test_data)

    def test_raises_file_not_found(self):
        """Raises FileNotFoundError when the JSON file does not exist."""
        nonexistent = os.path.join(self.test_dir, "nonexistent.json")
        with self.assertRaises(FileNotFoundError) as ctx:
            load_json_file(nonexistent)
        self.assertIn("JSON file not found", str(ctx.exception))
        self.assertIn(nonexistent, str(ctx.exception))

    def test_raises_json_decode_error_for_malformed_json(self):
        """Raises JSONDecodeError when the file contains invalid JSON."""
        with open(self.json_file, "w", encoding="utf-8") as f:
            f.write('{"invalid": json syntax')
        with self.assertRaises(json.JSONDecodeError):
            load_json_file(self.json_file)


@pytest.mark.unit
class TestLoadSvgFiles(unittest.TestCase):
    """Tests for the _load_svg_files function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.svg_folder = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_folder)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_svg(self, name):
        path = os.path.join(self.svg_folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("<svg></svg>")

    def test_returns_svg_filenames(self):
        """Returns a list of SVG filenames found in the folder."""
        self._create_svg("a.svg")
        self._create_svg("b.svg")
        result = _load_svg_files(self.svg_folder)
        self.assertIn("a.svg", result)
        self.assertIn("b.svg", result)
        self.assertEqual(len(result), 2)

    def test_raises_file_not_found_for_missing_folder(self):
        """Raises FileNotFoundError when the SVG folder does not exist."""
        nonexistent = os.path.join(self.test_dir, "nonexistent")
        with self.assertRaises(FileNotFoundError) as ctx:
            _load_svg_files(nonexistent)
        self.assertIn("SVG folder not found", str(ctx.exception))
        self.assertIn(nonexistent, str(ctx.exception))

    def test_raises_value_error_when_no_svg_files(self):
        """Raises ValueError when the folder contains no SVG files."""
        with open(os.path.join(self.svg_folder, "not_svg.txt"), "w", encoding="utf-8") as f:
            f.write("text")
        with self.assertRaises(ValueError) as ctx:
            _load_svg_files(self.svg_folder)
        self.assertIn("No SVG files found in folder", str(ctx.exception))
        self.assertIn(self.svg_folder, str(ctx.exception))

    def test_raises_permission_error_on_os_error(self):
        """Wraps OSError from os.listdir as PermissionError."""
        with patch("os.listdir", side_effect=OSError("Permission denied")):
            with self.assertRaises(PermissionError) as ctx:
                _load_svg_files(self.svg_folder)
        self.assertIn("Cannot list contents of SVG folder", str(ctx.exception))
        self.assertIn("Permission denied", str(ctx.exception))

    def test_detection_is_case_insensitive(self):
        """SVG file detection is case-insensitive (.svg, .SVG, .Svg)."""
        for i, ext in enumerate([".svg", ".SVG", ".Svg", ".sVg"]):
            self._create_svg(f"test{i}{ext}")
        result = _load_svg_files(self.svg_folder)
        self.assertEqual(len(result), 4)

    def test_filters_non_svg_files(self):
        """Only SVG files are returned; other extensions are ignored."""
        self._create_svg("image.svg")
        self._create_svg("another.SVG")
        for name in ["doc.txt", "script.py", "data.json", "readme.md"]:
            with open(os.path.join(self.svg_folder, name), "w", encoding="utf-8") as f:
                f.write("content")
        result = _load_svg_files(self.svg_folder)
        self.assertEqual(len(result), 2)
        self.assertIn("image.svg", result)
        self.assertIn("another.SVG", result)


@pytest.mark.unit
class TestLoadAndValidateInputs(unittest.TestCase):
    """Tests for the load_and_validate_inputs composition function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.svg_folder = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_folder)
        self.test_data = {
            "textcritics": [
                {
                    "id": "M143_TF1",
                    "commentary": {
                        "comments": [{"blockComments": [{"svgGroupId": "old-id-1"}]}]
                    },
                }
            ]
        }
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_svg(self, name, content='<svg></svg>'):
        with open(os.path.join(self.svg_folder, name), "w", encoding="utf-8") as f:
            f.write(content)

    @patch("sys.stdout", new_callable=StringIO)
    def test_returns_data_and_svg_files(self, _mock_stdout):
        """Returns the parsed JSON data and the list of SVG filenames."""
        self._create_svg("test1.svg")
        self._create_svg("test2.SVG")
        data, svg_files = load_and_validate_inputs(self.json_file, self.svg_folder)
        self.assertEqual(data, self.test_data)
        self.assertIn("test1.svg", svg_files)
        self.assertIn("test2.SVG", svg_files)

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_entry_and_svg_counts(self, mock_stdout):
        """Prints the number of textcritics entries and SVG files found."""
        self._create_svg("test1.svg")
        self._create_svg("test2.svg")
        load_and_validate_inputs(self.json_file, self.svg_folder)
        output = mock_stdout.getvalue()
        self.assertIn("Loaded JSON with 1 textcritics entries", output)
        self.assertIn("Found 2 SVG files", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_nested_data_prints_nested_count(self, mock_stdout):
        """Non-dict root data is printed with 'nested' as the entry count."""
        nested_data = [{"id": "M123_TF1", "commentary": {"comments": []}}]
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(nested_data, f)
        self._create_svg("test.svg")
        data, _ = load_and_validate_inputs(self.json_file, self.svg_folder)
        self.assertEqual(data, nested_data)
        self.assertIn("Loaded JSON with nested textcritics entries", mock_stdout.getvalue())


@pytest.mark.unit
class TestCreateSvgLoader(unittest.TestCase):
    """Test cases for the create_svg_loader function"""

    def setUp(self):
        """Set up temporary test directory and files"""
        self.test_dir = tempfile.mkdtemp()
        self.svg_folder = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_folder)

        # Create test SVG files
        self.svg1_content = '<svg><g id="test1" class="tkk"></g></svg>'
        self.svg2_content = '<svg><g id="test2" class="tkk other-class"></g></svg>'

        self.svg1_path = os.path.join(self.svg_folder, "test1.svg")
        self.svg2_path = os.path.join(self.svg_folder, "test2.svg")

        with open(self.svg1_path, "w", encoding="utf-8") as f:
            f.write(self.svg1_content)
        with open(self.svg2_path, "w", encoding="utf-8") as f:
            f.write(self.svg2_content)

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_svg_loader_basic_functionality(self):
        """Test basic SVG loading functionality"""
        svg_file_cache = {}

        get_svg_text = create_svg_loader(self.svg_folder, svg_file_cache)

        # Load first SVG
        svg_data = get_svg_text("test1.svg")

        self.assertIsNotNone(svg_data["svg_root"])
        self.assertEqual(svg_data["svg_root"].find(".//g").get("id"), "test1")
        self.assertEqual(svg_data["path"], self.svg1_path)
        self.assertFalse(svg_data["dirty"])
        self.assertFalse(svg_data["has_xml_declaration"])

        # Verify caching
        self.assertIn("test1.svg", svg_file_cache)
        self.assertEqual(svg_file_cache["test1.svg"], svg_data)

    def test_create_svg_loader_caching_behavior(self):
        """Test that SVG loader caches files and doesn't reload them"""
        svg_file_cache = {}

        get_svg_text = create_svg_loader(self.svg_folder, svg_file_cache)

        # Load same file multiple times
        svg_data1 = get_svg_text("test1.svg")
        svg_data2 = get_svg_text("test1.svg")

        # Should return same object reference (cached)
        self.assertIs(svg_data1, svg_data2)

        # Verify only one entry in cache
        self.assertEqual(len(svg_file_cache), 1)

    def test_create_svg_loader_multiple_files(self):
        """Test loading multiple different SVG files"""
        svg_file_cache = {}

        get_svg_text = create_svg_loader(self.svg_folder, svg_file_cache)

        # Load different files
        svg1_data = get_svg_text("test1.svg")
        svg2_data = get_svg_text("test2.svg")

        # Verify both are loaded correctly
        self.assertEqual(svg1_data["svg_root"].find(".//g").get("id"), "test1")
        self.assertEqual(svg2_data["svg_root"].find(".//g").get("id"), "test2")

        # Verify both are cached
        self.assertEqual(len(svg_file_cache), 2)

        # Verify they are different objects
        self.assertIsNot(svg1_data, svg2_data)


@pytest.mark.unit
class TestSaveOperations(unittest.TestCase):
    """Test cases for save operation functions"""

    def setUp(self):
        """Set up temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.svg_file = os.path.join(self.test_dir, "test.svg")

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_svg_files(self):
        """Test saving SVG files from loaded cache"""
        # Create test SVG content
        original_content = '<svg><g id="old-id" class="tkk"></g></svg>'
        updated_content = '<svg><g id="new-id" class="tkk"></g></svg>'

        svg_root, _ = _parse_svg_xml(updated_content)

        # Create loaded SVG texts structure
        loaded_svg_texts = {
            "test.svg": {
                "svg_root": svg_root,
                "path": self.svg_file,
                "has_xml_declaration": False,
                "dirty": True,
            }
        }

        # Write original content to file
        with open(self.svg_file, "w", encoding="utf-8") as f:
            f.write(original_content)

        # Save using function
        _save_svg_files(loaded_svg_texts)

        # Verify file was updated
        with open(self.svg_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        self.assertIn('id="new-id"', saved_content)
        self.assertNotEqual(saved_content, original_content)

    def test_save_svg_files_skips_non_dirty_files(self):
        """Test that non-dirty cached SVG files are not written."""
        original_content = '<svg><g id="old-id" class="tkk"></g></svg>'
        svg_root, _ = _parse_svg_xml('<svg><g id="new-id" class="tkk"></g></svg>')

        loaded_svg_texts = {
            "test.svg": {
                "svg_root": svg_root,
                "path": self.svg_file,
                "has_xml_declaration": False,
                "dirty": False,
            }
        }

        with open(self.svg_file, "w", encoding="utf-8") as f:
            f.write(original_content)

        _save_svg_files(loaded_svg_texts)

        with open(self.svg_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        self.assertEqual(saved_content, original_content)

    def test_save_json_file_formats_correctly(self):
        """Test saving JSON data with proper formatting"""
        test_data = {
            "textcritics": [
                {
                    "id": "M143_TF1",
                    "commentary": {
                        "comments": [
                            {"blockComments": [{"svgGroupId": "awg-tkk-m32_Sk1-001"}]}
                        ]
                    },
                }
            ]
        }

        # Save JSON
        save_json_file(test_data, self.json_file)

        # Verify file was saved correctly
        self.assertTrue(os.path.exists(self.json_file))

        # Load and verify content
        with open(self.json_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, test_data)

        # Verify formatting (indented)
        with open(self.json_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('    "textcritics"', content)  # Should be indented
        self.assertIn("        {", content)  # Nested indentation

    def test_save_results_integration(self):
        """Test the save_results function integration"""
        # Prepare test data
        test_data = {"textcritics": [{"id": "test", "commentary": {"comments": []}}]}
        svg_root, _ = _parse_svg_xml(
            '<svg><g id="awg-tkk-m32_Sk1-001" class="tkk"></g></svg>'
        )
        svg_file_cache = {
            "test.svg": {
                "svg_root": svg_root,
                "path": self.svg_file,
                "has_xml_declaration": False,
                "dirty": True,
            }
        }

        # Create original SVG file
        with open(self.svg_file, "w", encoding="utf-8") as f:
            f.write('<svg><g id="old-id" class="tkk"></g></svg>')

        # Call save_results
        save_results(test_data, svg_file_cache, self.json_file)

        # Verify SVG file was saved
        with open(self.svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()
        self.assertIn('id="awg-tkk-m32_Sk1-001"', svg_content)
        self.assertIn('class="tkk"', svg_content)

        # Verify JSON file was saved
        with open(self.json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        self.assertEqual(json_data, test_data)


@pytest.mark.unit
class TestSerializeSvgXML(unittest.TestCase):
    """Test cases for the _serialize_svg_xml helper."""

    def test_serialize_svg_xml_with_xml_declaration_and_newline(self):
        """Test that serialized SVG includes declaration and EOF newline by default."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root)

        self.assertTrue(result.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertTrue(result.endswith("\n"))

    def test_serialize_svg_xml_without_xml_declaration(self):
        """Test that serialized SVG omits XML declaration when not requested."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root, include_xml_declaration=False)

        self.assertFalse(result.lstrip().startswith("<?xml"))
        self.assertTrue(result.endswith("\n"))

    def test_serialize_svg_xml_normalizes_declaration_quotes_and_encoding_case(self):
        """Test that XML declaration uses double quotes and UTF-8 casing."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root)

        declaration = result.split("?>", 1)[0] + "?>"
        self.assertIn('version="1.0"', declaration)
        self.assertIn('encoding="UTF-8"', declaration)
        self.assertNotIn("'", declaration)

    def test_serialize_svg_xml_removes_whitespace_before_self_closing_tags(self):
        """Test that self-closing tags do not have a space before '/>'."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g /></svg>')

        result = _serialize_svg_xml(root)

        self.assertNotIn(" />", result)


@pytest.mark.unit
class TestParseSvgXML(unittest.TestCase):
    """Test cases for the _parse_svg_xml helper."""

    def test_parse_svg_xml_valid_xml_returns_root_and_no_error(self):
        """Test that valid SVG returns a root element and no error."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>'

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNotNone(root)
        self.assertIsNone(error)
        self.assertTrue(root.tag.endswith("svg"))

    def test_parse_svg_xml_invalid_xml_returns_error(self):
        """Test that invalid XML returns no root and a parse error message."""
        svg_content = "<svg><g></svg>"

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNone(root)
        self.assertIsNotNone(error)
        self.assertTrue(error.startswith("XML parse error:"))

    def test_parse_svg_xml_with_declaration_and_leading_whitespace(self):
        """Test that declaration after leading whitespace is rejected."""
        svg_content = (
            ' \n\t<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>'
        )

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNone(root)
        self.assertIsNotNone(error)
        self.assertTrue(error.startswith("XML parse error:"))


if __name__ == "__main__":
    unittest.main()
