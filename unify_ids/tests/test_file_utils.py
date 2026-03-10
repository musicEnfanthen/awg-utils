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
from unittest.mock import patch
from io import StringIO
import pytest

# Import the functions we want to test
from utils.file_utils import (
    load_and_validate_inputs,
    create_svg_loader,
    save_results,
    save_svg_files,
    save_json_file
)


@pytest.mark.unit
class TestLoadAndValidateInputs(unittest.TestCase):
    """Test cases for the load_and_validate_inputs function"""

    def setUp(self):
        """Set up temporary directories and files for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.svg_folder = os.path.join(self.test_dir, "svgs")

        # Create SVG folder
        os.makedirs(self.svg_folder)

        # Create valid JSON test data
        self.test_data = {
            "textcritics": [
                {
                    "id": "M_143_TF1",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }

        # Write valid JSON file
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        """Clean up temporary files and directories"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_and_validate_inputs_success(self):
        """Test successful loading with valid inputs"""
        # Create test SVG files
        svg1 = os.path.join(self.svg_folder, "test1.svg")
        svg2 = os.path.join(self.svg_folder, "test2.SVG")  # Test case insensitive

        with open(svg1, 'w', encoding='utf-8') as f:
            f.write('<svg><g id="test1" class="tkk"></g></svg>')
        with open(svg2, 'w', encoding='utf-8') as f:
            f.write('<svg><g id="test2" class="tkk"></g></svg>')

        # Capture prints
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            data, svg_files = load_and_validate_inputs(self.json_file, self.svg_folder)

        # Verify returned data
        self.assertEqual(data, self.test_data)
        self.assertEqual(len(svg_files), 2)
        self.assertIn("test1.svg", svg_files)
        self.assertIn("test2.SVG", svg_files)

        # Verify printed messages
        output = mock_stdout.getvalue()
        self.assertIn("Loaded JSON with 1 textcritics entries", output)
        self.assertIn("Found 2 SVG files", output)

    def test_load_and_validate_inputs_with_json_not_found(self):
        """Test FileNotFoundError when JSON file doesn't exist"""
        nonexistent_json = os.path.join(self.test_dir, "nonexistent.json")

        with self.assertRaises(FileNotFoundError) as context:
            load_and_validate_inputs(nonexistent_json, self.svg_folder)

        self.assertIn("JSON file not found", str(context.exception))
        self.assertIn(nonexistent_json, str(context.exception))

    def test_load_and_validate_inputs_with_svg_folder_not_found(self):
        """Test FileNotFoundError when SVG folder doesn't exist"""
        nonexistent_folder = os.path.join(self.test_dir, "nonexistent")

        with self.assertRaises(FileNotFoundError) as context:
            load_and_validate_inputs(self.json_file, nonexistent_folder)

        self.assertIn("SVG folder not found", str(context.exception))
        self.assertIn(nonexistent_folder, str(context.exception))

    def test_load_and_validate_inputs_no_svg_files(self):
        """Test ValueError when no SVG files found in folder"""
        # Create non-SVG files
        txt_file = os.path.join(self.svg_folder, "not_svg.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("Not an SVG file")

        with self.assertRaises(ValueError) as context:
            load_and_validate_inputs(self.json_file, self.svg_folder)

        self.assertIn("No SVG files found in folder", str(context.exception))
        self.assertIn(self.svg_folder, str(context.exception))

    def test_load_and_validate_inputs_with_invalid_json(self):
        """Test JSON parsing error with malformed JSON"""
        # Write invalid JSON
        with open(self.json_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json syntax')

        with self.assertRaises(json.JSONDecodeError):
            load_and_validate_inputs(self.json_file, self.svg_folder)

    def test_load_and_validate_inputs_with_permission_error(self):
        """Test PermissionError when cannot list directory contents"""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.side_effect = OSError("Permission denied")

            with self.assertRaises(PermissionError) as context:
                load_and_validate_inputs(self.json_file, self.svg_folder)

            self.assertIn("Cannot list contents of SVG folder", str(context.exception))
            self.assertIn("Permission denied", str(context.exception))

    def test_load_and_validate_inputs_with_nested_data_structure(self):
        """Test with nested data structure (non-dict at root level)"""
        # Create nested data structure
        nested_data = [
            {
                "id": "M_123_TF1",
                "commentary": {"comments": []}
            }
        ]

        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(nested_data, f)

        # Create SVG file
        svg_file = os.path.join(self.svg_folder, "test.svg")
        with open(svg_file, 'w', encoding='utf-8') as f:
            f.write('<svg></svg>')

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            data, svg_files = load_and_validate_inputs(self.json_file, self.svg_folder)

        self.assertEqual(data, nested_data)
        self.assertEqual(len(svg_files), 1)

        # Check that it handles nested structure in print statement
        output = mock_stdout.getvalue()
        self.assertIn("Loaded JSON with nested textcritics entries", output)

    def test_load_and_validate_inputs_with_case_insensitive_svg_detection(self):
        """Test that SVG file detection is case insensitive"""
        # Create SVG files with different case extensions
        extensions = [".svg", ".SVG", ".Svg", ".sVg"]
        for i, ext in enumerate(extensions):
            svg_file = os.path.join(self.svg_folder, f"test{i}{ext}")
            with open(svg_file, 'w', encoding='utf-8') as f:
                f.write('<svg></svg>')

        _, svg_files = load_and_validate_inputs(self.json_file, self.svg_folder)

        self.assertEqual(len(svg_files), 4)
        for i, ext in enumerate(extensions):
            self.assertIn(f"test{i}{ext}", svg_files)

    def test_load_and_validate_inputs_with_mixed_file_types(self):
        """Test with mixed file types, only SVG files should be included"""
        # Create various file types
        file_types = [
            ("image.svg", "svg content"),
            ("document.txt", "text content"),
            ("script.py", "python content"),
            ("data.json", "json content"),
            ("another.SVG", "svg content"),
            ("readme.md", "markdown content")
        ]

        for filename, content in file_types:
            filepath = os.path.join(self.svg_folder, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        _, svg_files = load_and_validate_inputs(self.json_file, self.svg_folder)

        # Only SVG files should be included
        self.assertEqual(len(svg_files), 2)
        self.assertIn("image.svg", svg_files)
        self.assertIn("another.SVG", svg_files)
        self.assertNotIn("document.txt", svg_files)
        self.assertNotIn("script.py", svg_files)


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

        with open(self.svg1_path, 'w', encoding='utf-8') as f:
            f.write(self.svg1_content)
        with open(self.svg2_path, 'w', encoding='utf-8') as f:
            f.write(self.svg2_content)

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_svg_loader_basic_functionality(self):
        """Test basic SVG loading functionality"""
        final_svg_cache = {}
        loaded_svg_texts = {}

        get_svg_text = create_svg_loader(self.svg_folder, final_svg_cache, loaded_svg_texts)

        # Load first SVG
        svg_data = get_svg_text("test1.svg")

        self.assertEqual(svg_data["content"], self.svg1_content)
        self.assertEqual(svg_data["path"], self.svg1_path)

        # Verify caching
        self.assertIn("test1.svg", loaded_svg_texts)
        self.assertIn("test1.svg", final_svg_cache)
        self.assertEqual(loaded_svg_texts["test1.svg"], svg_data)
        self.assertEqual(final_svg_cache["test1.svg"], svg_data)

    def test_create_svg_loader_caching_behavior(self):
        """Test that SVG loader caches files and doesn't reload them"""
        final_svg_cache = {}
        loaded_svg_texts = {}

        get_svg_text = create_svg_loader(self.svg_folder, final_svg_cache, loaded_svg_texts)

        # Load same file multiple times
        svg_data1 = get_svg_text("test1.svg")
        svg_data2 = get_svg_text("test1.svg")

        # Should return same object reference (cached)
        self.assertIs(svg_data1, svg_data2)

        # Verify only one entry in cache
        self.assertEqual(len(loaded_svg_texts), 1)
        self.assertEqual(len(final_svg_cache), 1)

    def test_create_svg_loader_multiple_files(self):
        """Test loading multiple different SVG files"""
        final_svg_cache = {}
        loaded_svg_texts = {}

        get_svg_text = create_svg_loader(self.svg_folder, final_svg_cache, loaded_svg_texts)

        # Load different files
        svg1_data = get_svg_text("test1.svg")
        svg2_data = get_svg_text("test2.svg")

        # Verify both are loaded correctly
        self.assertEqual(svg1_data["content"], self.svg1_content)
        self.assertEqual(svg2_data["content"], self.svg2_content)

        # Verify both are cached
        self.assertEqual(len(loaded_svg_texts), 2)
        self.assertEqual(len(final_svg_cache), 2)

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

        # Create loaded SVG texts structure
        loaded_svg_texts = {
            "test.svg": {
                "content": updated_content,
                "path": self.svg_file
            }
        }

        # Write original content to file
        with open(self.svg_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # Save using function
        save_svg_files(loaded_svg_texts)

        # Verify file was updated
        with open(self.svg_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()

        self.assertEqual(saved_content, updated_content)
        self.assertNotEqual(saved_content, original_content)

    def test_save_json_file(self):
        """Test saving JSON data with proper formatting"""
        test_data = {
            "textcritics": [
                {
                    "id": "M_143_TF1",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "g-tkk-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }

        # Save JSON
        save_json_file(test_data, self.json_file)

        # Verify file was saved correctly
        self.assertTrue(os.path.exists(self.json_file))

        # Load and verify content
        with open(self.json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, test_data)

        # Verify formatting (indented)
        with open(self.json_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('    "textcritics"', content)  # Should be indented
        self.assertIn('        {', content)  # Nested indentation

    def test_save_results_integration(self):
        """Test the save_results function integration"""
        # Prepare test data
        test_data = {"textcritics": [{"id": "test", "commentary": {"comments": []}}]}
        loaded_svg_texts = {
            "test.svg": {
                "content": '<svg><g id="g-tkk-1" class="tkk"></g></svg>',
                "path": self.svg_file
            }
        }

        # Create original SVG file
        with open(self.svg_file, 'w', encoding='utf-8') as f:
            f.write('<svg><g id="old-id" class="tkk"></g></svg>')

        # Call save_results with new signature
        save_results(test_data, loaded_svg_texts, self.json_file)

        # Verify SVG file was saved
        with open(self.svg_file, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        self.assertEqual(svg_content, '<svg><g id="g-tkk-1" class="tkk"></g></svg>')

        # Verify JSON file was saved
        with open(self.json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        self.assertEqual(json_data, test_data)


if __name__ == '__main__':
    unittest.main()
