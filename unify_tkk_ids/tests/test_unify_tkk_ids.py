#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for unify_tkk_ids.py

Tests for TKK Group ID unification functionality including:
- Number extraction from text
- ID validation and error reporting
- JSON and SVG processing logic
- SkRT special logic handling
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, mock_open
from io import StringIO
import pytest

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from unify_tkk_ids import (
    extract_moldenhauer_number, 
    display_uncertainties, 
    get_relevant_svgs, 
    update_svg_id, 
    process_tkk_ids
)


@pytest.mark.unit
class TestExtractMoldenhauerNumber(unittest.TestCase):
    """Test cases for the extract_moldenhauer_number function"""
    
    def test_extract_moldenhauer_number_from_simple_id(self):
        """Test extracting Moldenhauer numbers from simple ID strings"""
        self.assertEqual(extract_moldenhauer_number("M_143"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123"), "123")
    
    def test_extract_moldenhauer_number_from_structured_id(self):
        """Test extracting Moldenhauer number from structured ID strings"""
        self.assertEqual(extract_moldenhauer_number("M_143_TF5"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123_Sk456"), "123")  # Only first number after Mx
        self.assertEqual(extract_moldenhauer_number("M_789_op1_test2"), "789")

    def test_extract_moldenhauer_number_from_filename_without_underscore(self):
        """Test extracting Moldenhauer numbers from filename patterns without underscore after M/Mx"""
        self.assertEqual(extract_moldenhauer_number("M143_Textfassung1"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx136_Sk1"), "136")
        self.assertEqual(extract_moldenhauer_number("M789_file"), "789")
        self.assertEqual(extract_moldenhauer_number("M14_test"), "14")
        # Mixed patterns - should still work with existing underscore patterns
        self.assertEqual(extract_moldenhauer_number("M_143_TF1"), "143")  # With underscore still works
        self.assertEqual(extract_moldenhauer_number("M143TF1"), "143")    # No separators at all
    
    def test_extract_moldenhauer_number_with_no_moldenhauer_pattern(self):
        """Test ID strings with no M/Mx pattern"""
        self.assertEqual(extract_moldenhauer_number("no_pattern_here"), "")
        self.assertEqual(extract_moldenhauer_number("abc_def"), "")
        self.assertEqual(extract_moldenhauer_number(""), "")
        self.assertEqual(extract_moldenhauer_number("123456"), "")  # No M/Mx prefix
    
    def test_extract_moldenhauer_number_with_none_input(self):
        """Test with None input (converted to string)"""
        self.assertEqual(extract_moldenhauer_number(None), "")  # 'None' string doesn't match M/Mx pattern

    
@pytest.mark.unit
class TestDisplayUncertainties(unittest.TestCase):
    """Test cases for the display_uncertainties function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "g-tkk-"
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_with_no_errors(self, mock_stdout):
        """Test with all IDs correctly prefixed"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "g-tkk-1"},
                                    {"svgGroupId": "g-tkk-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {
            "test.svg": {
                "content": '<g class="tkk" id="g-tkk-1">content</g>'
            }
        }
        
        display_uncertainties(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_with_json_errors(self, mock_stdout):
        """Test with unchanged JSON IDs"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "g-tkk-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {}
        
        display_uncertainties(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("JSON ERROR: Unchanged ID 'old-id-1'", output)
        self.assertIn("Total issues found: 1", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_with_svg_orphans(self, mock_stdout):
        """Test with SVG IDs that weren't updated"""
        data = {"textcritics": []}
        
        loaded_svgs = {
            "test.svg": {
                "content": '<g class="tkk" id="old-svg-id">content</g>'
            }
        }
        
        display_uncertainties(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("SVG ORPHAN: ID 'old-svg-id'", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_with_todo_ignored(self, mock_stdout):
        """Test that TODO entries are ignored"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "TODO"},
                                    {"svgGroupId": "g-tkk-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {}
        
        display_uncertainties(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)


@pytest.mark.unit
class TestGetRelevantSvgs(unittest.TestCase):
    """Test cases for the get_relevant_svgs function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.all_svg_files = [
            "M143_Textfassung1-1von2-final.svg",
            "M143_Textfassung1-2von2-final.svg",
            "M143_Textfassung2-1von1-final.svg",
            "M143_Sk1-1von1-final.svg",
            "M143_Sk2_1-1von1-final.svg",
            "M143_Sk2_1_1_1-1von1-final.svg",
            "M143_Sk2_2-1von1-final.svg",
            "M143_Sk2-1von3-final.svg",
            "M143_Sk2-2von3-final.svg",
            "M143_Sk2-3von3-final.svg",
            "op25_C_Reihentabelle-1von1-final.svg",
            "M144_sheet1.svg",
            "M145_other.svg"
        ]
    
    def test_get_relevant_svgs_for_TF1(self):
        """Test getting SVGs for for TF1 entries"""
        result = get_relevant_svgs("M_143_TF1", self.all_svg_files, "143")
        # Should only get Textfassung1 files, not Textfassung2
        expected = ["M143_Textfassung1-1von2-final.svg", "M143_Textfassung1-2von2-final.svg"]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_standard_for_TF2(self):
        """Test getting SVGs for TF2 entries"""
        result = get_relevant_svgs("M_143_TF2", self.all_svg_files, "143")
        # Should only get Textfassung2 files
        expected = ["M143_Textfassung2-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_for_Sk2(self):
        """Test getting SVGs for Sk2 entries"""
        result = get_relevant_svgs("M_143_Sk2", self.all_svg_files, "143")
        # Should only get Sk2 files (not Sk2_1, Sk2_2, etc.)
        expected = [
            "M143_Sk2-1von3-final.svg", 
            "M143_Sk2-2von3-final.svg", 
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_for_Sk2_1(self):
        """Test getting SVGs for Sk2_1 entries (sub-numbered sketches)"""
        result = get_relevant_svgs("M_143_Sk2_1", self.all_svg_files, "143")
        # Should only get Sk2_1 files
        expected = ["M143_Sk2_1-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_for_Sk2_2(self):
        """Test getting SVGs for Sk2_2 entries"""  
        result = get_relevant_svgs("M_143_Sk2_2", self.all_svg_files, "143")
        # Should only get Sk2_2 files
        expected = ["M143_Sk2_2-1von1-final.svg"]
        self.assertEqual(result, expected)
        
    def test_get_relevant_svgs_for_Sk2_1_1_1(self):
        """Test getting SVGs for Sk2_1_1_1 entries (sub-numbered sketches)"""
        result = get_relevant_svgs("M_143_Sk2_1_1_1", self.all_svg_files, "143")
        # Should only get Sk2_1_1_1 files
        expected = ["M143_Sk2_1_1_1-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_no_tf_specified(self):
        """Test getting SVGs when no TF or Sk is specified - should get all non-Reihentabelle files"""
        result = get_relevant_svgs("M_143", self.all_svg_files, "143")
        # Should get all Textfassung files when no specific TF is mentioned
        expected = [
            "M143_Textfassung1-1von2-final.svg", 
            "M143_Textfassung1-2von2-final.svg", 
            "M143_Textfassung2-1von1-final.svg", 
            "M143_Sk1-1von1-final.svg", 
            "M143_Sk2_1-1von1-final.svg",
            "M143_Sk2_1_1_1-1von1-final.svg",
            "M143_Sk2_2-1von1-final.svg", 
            "M143_Sk2-1von3-final.svg", 
            "M143_Sk2-2von3-final.svg", 
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_skrt(self):
        """Test getting SVGs for SkRT entries"""
        result = get_relevant_svgs("SkRT", self.all_svg_files, "")
        expected = ["op25_C_Reihentabelle-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_get_relevant_svgs_no_matches(self):
        """Test getting SVGs when no matches exist"""
        result = get_relevant_svgs("M_999", self.all_svg_files, "999")
        self.assertEqual(result, [])
    
    def test_get_relevant_svgs_empty_file_list(self):
        """Test with empty SVG file list"""
        result = get_relevant_svgs("M_143", [], "143")
        self.assertEqual(result, [])


@pytest.mark.unit
class TestUpdateSvgId(unittest.TestCase):
    """Test cases for the update_svg_id function"""
    
    def test_update_svg_id_with_class_before_id(self):
        """Test updating SVG with class before id attribute"""
        svg_content = '<g class="tkk" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g class="tkk" id="new-id">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)
    
    def test_update_svg_id_with_id_before_class(self):
        """Test updating SVG with id before class attribute"""
        svg_content = '<g id="old-id" class="tkk">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g id="new-id" class="tkk">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)
    
    def test_update_svg_id_with_single_quotes(self):
        """Test updating SVG with single quotes"""
        svg_content = "<g class='tkk' id='old-id'>content</g>"
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = "<g class='tkk' id='new-id'>content</g>"
        self.assertEqual(result, expected)
        self.assertIsNone(error)
    
    def test_update_svg_id_with_no_class_tkk(self):
        """Test that IDs without class='tkk' are not updated"""
        svg_content = '<g class="other" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        self.assertEqual(result, svg_content)  # Should remain unchanged
        self.assertIsNone(error)
    
    def test_update_svg_id_with_multiple_occurrences(self):
        """Test that multiple class='tkk' elements with same ID cause an error"""
        svg_content = '''<svg>
    <g class="tkk" id="old-id">content1</g>
    <g id="old-id" class="tkk">content2</g>
    <g class="other" id="old-id">content3</g>
</svg>'''
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        
        # Should return unchanged content and error message
        self.assertEqual(result, svg_content)
        self.assertIsNotNone(error)
        self.assertIn("Multiple class='tkk' elements found with ID 'old-id'", error)
        self.assertIn("2 occurrences", error)  # Should find 2 tkk elements


@pytest.mark.integration
class TestProcessTkkIds(unittest.TestCase):
    """Integration tests for the process_tkk_ids function"""
    
    def setUp(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "textcritics.json")
        self.svg_dir = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_dir)
        
        # Create test JSON
        self.test_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [{
                            "blockComments": [
                                {"svgGroupId": "old-id-1"}
                            ]
                        }]
                    }
                }
            ]
        }
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_json, f)
        
        # Create test SVG
        self.svg_path = os.path.join(self.svg_dir, "M_143_test.svg")
        with open(self.svg_path, 'w', encoding='utf-8') as f:
            f.write('<g class="tkk" id="old-id-1">content</g>')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_process_tkk_ids_success(self, mock_stdout):
        """Test successful processing of TKK IDs"""
        data, svg_cache, success = process_tkk_ids(
            self.json_path, self.svg_dir, "g-tkk-"
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertIsNotNone(svg_cache)
        
        # Check that JSON was updated
        updated_id = data['textcritics'][0]['commentary']['comments'][0]['blockComments'][0]['svgGroupId']
        self.assertEqual(updated_id, "g-tkk-1")
    
    def test_process_tkk_ids_missing_json(self):
        """Test error handling for missing JSON file"""
        with self.assertRaises(FileNotFoundError):
            process_tkk_ids("/nonexistent/path.json", self.svg_dir)
    
    def test_process_tkk_ids_missing_svg_dir(self):
        """Test error handling for missing SVG directory"""
        with self.assertRaises(FileNotFoundError):
            process_tkk_ids(self.json_path, "/nonexistent/dir")


@pytest.mark.integration
class TestIntegration(unittest.TestCase):
    """Integration tests with temporary files"""
    
    def setUp(self):
        """Create temporary directory and test files"""
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "textcritics.json")
        self.svg_dir = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_dir)
        
        # Create test JSON data
        self.test_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "old-id-2"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "M_144_SkRT",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "skrt-old-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        # Write test JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_json, f)
        
        # Create test SVG files
        self.svg_143 = os.path.join(self.svg_dir, "M_143_test.svg")
        with open(self.svg_143, 'w', encoding='utf-8') as f:
            f.write('''<svg>
    <g class="tkk" id="old-id-1">content1</g>
    <g id="old-id-2" class="tkk">content2</g>
    <g class="other" id="other-id">other</g>
</svg>''')
        
        self.svg_144 = os.path.join(self.svg_dir, "M_144_Reihentabelle.svg")
        with open(self.svg_144, 'w', encoding='utf-8') as f:
            f.write('''<svg>
    <g class="tkk" id="skrt-old-1">SkRT content</g>
</svg>''')
    
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
    
    def test_file_structure_creation(self):
        """Test that test files are created correctly"""
        self.assertTrue(os.path.exists(self.json_path))
        self.assertTrue(os.path.exists(self.svg_dir))
        self.assertTrue(os.path.exists(self.svg_143))
        self.assertTrue(os.path.exists(self.svg_144))
    
    def test_json_loading(self):
        """Test loading the test JSON file"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('textcritics', data)
        self.assertEqual(len(data['textcritics']), 2)
        self.assertEqual(data['textcritics'][0]['id'], 'M_143')
        self.assertEqual(data['textcritics'][1]['id'], 'M_144_SkRT')
    
    def test_svg_file_detection(self):
        """Test SVG file detection and filtering"""
        svg_files = [f for f in os.listdir(self.svg_dir) if f.endswith('.svg')]
        self.assertEqual(len(svg_files), 2)
        self.assertIn('M_143_test.svg', svg_files)
        self.assertIn('M_144_Reihentabelle.svg', svg_files)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_extract_numbers_special_characters(self):
        """Test extract_numbers with special characters"""
        self.assertEqual(extract_numbers("M_143-op5.2"), "143")
        self.assertEqual(extract_numbers("Mx_123#test456$"), "123")
        self.assertEqual(extract_numbers("M_789_测试_123"), "789")
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_empty_data(self, mock_stdout):
        """Test display_uncertainties with empty data"""
        display_uncertainties({}, "g-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_uncertainties_malformed_json(self, mock_stdout):
        """Test display_uncertainties with malformed JSON structure"""
        data = {
            "textcritics": [
                {
                    # Missing commentary structure
                    "id": "M_143"
                },
                {
                    "id": "M_144",
                    "commentary": {
                        # Missing comments
                    }
                }
            ]
        }
        
        display_uncertainties(data, "g-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)


if __name__ == '__main__':
    # Create test data directory structure
    test_data_dir = os.path.join(os.path.dirname(__file__), 'tests')
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
        
        # Create sample data subdirectories
        data_dir = os.path.join(test_data_dir, 'data')
        img_dir = os.path.join(test_data_dir, 'img')
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)
        
        # Create sample textcritics.json
        sample_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "old-id-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        with open(os.path.join(data_dir, 'textcritics.json'), 'w', encoding='utf-8') as f:
            json.dump(sample_json, f, indent=2)
        
        # Create sample SVG
        sample_svg = '''<svg xmlns="http://www.w3.org/2000/svg">
    <g class="tkk" id="old-id-1">
        <text>Test content 1</text>
    </g>
    <g id="old-id-2" class="tkk">
        <text>Test content 2</text>
    </g>
</svg>'''
        
        with open(os.path.join(img_dir, 'M_143_test.svg'), 'w', encoding='utf-8') as f:
            f.write(sample_svg)
    
    unittest.main()