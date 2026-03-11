#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for extraction_utils.py module

This test suite provides comprehensive testing for the extraction utilities
used in TKK ID processing. The extraction_utils module handles extraction
and parsing of various identifiers and data structures.

Test Categories:
- extract_class_attr_value function tests (class attribute extraction from SVG tags)
- extract_id_suffix function tests (linkBox ID suffix extraction from SVG filenames)
- extract_link_boxes function tests (linkBox extraction from entries)
- extract_moldenhauer_number function tests (catalog number extraction)
- extract_svg_group_ids function tests (SVG group ID collection from entries)
- Edge cases and error conditions for extraction operations

Usage:
    pytest tests/test_extraction_utils.py -v
    pytest tests/test_extraction_utils.py::TestExtractClassAttrValue -v
    pytest tests/test_extraction_utils.py::TestExtractIdSuffix -v
    pytest tests/test_extraction_utils.py::TestExtractLinkBoxes -v
    pytest tests/test_extraction_utils.py::TestExtractMoldenhauerNumber -v
    pytest tests/test_extraction_utils.py::TestExtractSvgGroupIds -v
"""

import unittest
import pytest

# Import extraction functions from extraction_utils
from utils.extraction_utils import (
    extract_class_attr_value,
    extract_id_suffix,
    extract_link_boxes,
    extract_moldenhauer_number,
    extract_svg_group_ids,
    has_class_token
)


@pytest.mark.unit
class TestExtractClassAttrValue(unittest.TestCase):
    """Test cases for the extract_class_attr_value function"""

    def test_extract_class_attr_value_from_double_quotes(self):
        """Test extracting class attribute value from a tag with double quotes"""
        tag = '<g class="tkk other-class" id="foo">'
        self.assertEqual(extract_class_attr_value(tag), 'tkk other-class')

    def test_extract_class_attr_value_from_single_quotes(self):
        """Test extracting class attribute value from a tag with single quotes"""
        tag = "<rect class='link-box' id='bar'>"
        self.assertEqual(extract_class_attr_value(tag), 'link-box')

    def test_extract_class_attr_value_with_spaces(self):
        """Test extracting class attribute value from a tag with extra spaces"""
        tag = '<g   class =   "active tkk selected"   id="foo">'
        self.assertEqual(extract_class_attr_value(tag), 'active tkk selected')

    def test_extract_class_attr_value_with_no_class(self):
        """Test extracting class attribute value from a tag that has no class attribute"""
        tag = '<g id="foo">'
        self.assertEqual(extract_class_attr_value(tag), '')

    def test_extract_class_attr_value_with_empty_class(self):
        """Test extracting class attribute value from a tag with an empty class attribute"""
        tag = '<g class="" id="foo">'
        self.assertEqual(extract_class_attr_value(tag), '')

    def test_extract_class_attr_value_with_class_at_end(self):
        """Test extracting class attribute value from a tag where class is the last attribute"""
        tag = '<g id="foo" class="tkk">'
        self.assertEqual(extract_class_attr_value(tag), 'tkk')

    def test_extract_class_attr_value_with_multiple_attributes(self):
        """Test extracting class attribute value from a tag with multiple attributes"""
        tag = '<g class="tkk" data-x="1" id="foo">'
        self.assertEqual(extract_class_attr_value(tag), 'tkk')


@pytest.mark.unit
class TestExtractIdSuffix(unittest.TestCase):
    """Test cases for the extract_id_suffix function"""

    def test_extract_id_suffix_with_single_file_partial(self):
        """Test extracting suffix from a filename with '-1von1-' pattern"""
        self.assertEqual(extract_id_suffix('file-1von1-.svg'), '')
        self.assertEqual(extract_id_suffix('something-1von1-.svg'), '')

    def test_extract_id_suffix_with_multiple_file_partials(self):
        """Test extracting suffix from filenames with '-NvonM-' patterns"""
        self.assertEqual(extract_id_suffix('file-1von6-.svg'), 'a')
        self.assertEqual(extract_id_suffix('file-2von7-.svg'), 'b')
        self.assertEqual(extract_id_suffix('file-3von5-.svg'), 'c')
        self.assertEqual(extract_id_suffix('file-4von8-.svg'), 'd')
        self.assertEqual(extract_id_suffix('file-5von9-.svg'), 'e')
        self.assertEqual(extract_id_suffix('file-6von6-.svg'), 'f')
        self.assertEqual(extract_id_suffix('file-9von12-.svg'), 'i')
        self.assertEqual(extract_id_suffix('file-15von15-.svg'), 'o')

    def test_extract_id_suffix_with_pattern_not_found(self):
        """Test extracting suffix from filenames that do not match the pattern"""
        self.assertEqual(extract_id_suffix('file-no-pattern.svg'), 'x')
        self.assertEqual(extract_id_suffix('file-abcvonxyz-.svg'), 'x')
        self.assertEqual(extract_id_suffix('file-.svg'), 'x')

    def test_extract_id_suffix_edge_cases(self):
        """Test extracting suffix from edge case filenames"""
        self.assertEqual(extract_id_suffix('file-0von1-.svg'), '`')  # 0->chr(ord('a')-1)
        self.assertEqual(extract_id_suffix('file-1von0-.svg'), 'a')  # total=0, num=1
        self.assertEqual(extract_id_suffix('file-100von100-.svg'), 'Ä')  # 100->chr(ord('a')+99)


@pytest.mark.unit
class TestExtractLinkBoxes(unittest.TestCase):
    """Test cases for the extract_link_boxes function"""

    def test_extract_link_boxes_normal(self):
        """Test extracting linkBoxes from a normal entry structure"""
        entry = {
            'linkBoxes': [
                {'svgGroupId': 'g1', 'linkTo': 'foo'},
                {'svgGroupId': 'g2', 'linkTo': 'bar'}
            ]
        }
        result = extract_link_boxes(entry)
        self.assertEqual(result, [
            {'svgGroupId': 'g1', 'linkTo': 'foo'},
            {'svgGroupId': 'g2', 'linkTo': 'bar'}
        ])

    def test_extract_link_boxes_with_missing_key(self):
        """Test extracting linkBoxes when the key is missing"""
        entry = {}
        result = extract_link_boxes(entry)
        self.assertEqual(result, [])

    def test_extract_link_boxes_with_wrong_type(self):
        """Test extracting linkBoxes when the key is not a list"""
        entry = {'linkBoxes': 'not-a-list'}
        result = extract_link_boxes(entry)
        self.assertEqual(result, [])

    def test_extract_link_boxes_empty(self):
        """Test extracting linkBoxes when the list is empty"""
        entry = {'linkBoxes': []}
        result = extract_link_boxes(entry)
        self.assertEqual(result, [])


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
        self.assertEqual(extract_moldenhauer_number("Mx_123_Sk456"), "123")
        self.assertEqual(extract_moldenhauer_number("M_789_op1_test2"), "789")

    def test_extract_moldenhauer_number_from_filename_without_underscore(self):
        """Test extracting numbers from filename patterns without underscore after M/Mx"""
        self.assertEqual(extract_moldenhauer_number("M143_Textfassung1"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx136_Sk1"), "136")
        self.assertEqual(extract_moldenhauer_number("M789_file"), "789")
        self.assertEqual(extract_moldenhauer_number("M14_test"), "14")
        # Mixed patterns - should still work with existing underscore patterns
        self.assertEqual(extract_moldenhauer_number("M_143_TF1"), "143")
        self.assertEqual(extract_moldenhauer_number("M143TF1"), "143")

    def test_extract_moldenhauer_number_with_no_moldenhauer_pattern(self):
        """Test ID strings with no M/Mx pattern"""
        self.assertEqual(extract_moldenhauer_number("no_pattern_here"), "")
        self.assertEqual(extract_moldenhauer_number("abc_def"), "")
        self.assertEqual(extract_moldenhauer_number(""), "")
        self.assertEqual(extract_moldenhauer_number("123456"), "")  # No M/Mx prefix

    def test_extract_moldenhauer_number_with_none_input(self):
        """Test with None input (converted to string)"""
        self.assertEqual(extract_moldenhauer_number(None), "")

    def test_extract_moldenhauer_number_with_special_characters(self):
        """Test extract_moldenhauer_numbers with special characters"""
        self.assertEqual(extract_moldenhauer_number("M_143-op5.2"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123#test456$"), "123")
        self.assertEqual(extract_moldenhauer_number("M_789_测试_123"), "789")


@pytest.mark.unit
class TestExtractSvgGroupIds(unittest.TestCase):
    """Test cases for the extract_svg_group_ids function"""

    def test_extract_svg_group_ids_basic(self):
        """Test extracting svgGroupIds from a basic entry structure"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)
        self.assertEqual(block_comments[0]["svgGroupId"], "test-id-1")
        self.assertEqual(block_comments[1]["svgGroupId"], "test-id-2")

    def test_extract_svg_group_ids_with_multiple_comment_groups(self):
        """Test extracting svgGroupIds from multiple comment groups"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "id-1", "text": "Comment 1"},
                            {"svgGroupId": "id-2", "text": "Comment 2"}
                        ]
                    },
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "id-3", "text": "Comment 3"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        expected_ids = ["id-1", "id-2", "id-3"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 3)

    def test_extract_svg_group_ids_with_todo_entries(self):
        """Test that TODO entries are filtered out"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "TODO", "text": "TODO Comment"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # The TODO entries should be filtered out
        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)

        # Verify that TODO block comment is not included
        for comment in block_comments:
            self.assertNotEqual(comment["svgGroupId"], "TODO")

    def test_extract_svg_group_ids_with_empty_ids(self):
        """Test that empty or None svgGroupId entries are filtered out"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "", "text": "Empty ID"},
                            {"svgGroupId": None, "text": "None ID"},
                            {"text": "No svgGroupId field"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # Only valid IDs should be included
        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)

    def test_extract_svg_group_ids_with_no_commentary(self):
        """Test entry with no commentary section"""
        entry = {"id": "M_143_TF1"}

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_with_no_comments(self):
        """Test entry with commentary but no comments"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {"preamble": "", "comments": []}
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_with_no_block_comments(self):
        """Test entry with comments but no blockComments"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {"blockHeader": "", "blockComments": []},
                    {"blockHeader": "", "otherField": "value"}
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_preserves_order(self):
        """Test that the order of svgGroupIds is preserved"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "z-last", "text": "Should be first"},
                            {"svgGroupId": "a-first", "text": "Should be second"},
                            {"svgGroupId": "m-middle", "text": "Should be third"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # Should preserve original order, not alphabetical
        expected_ids = ["z-last", "a-first", "m-middle"]
        self.assertEqual(svg_group_ids, expected_ids)

        # Block comments should be in same order
        self.assertEqual(block_comments[0]["svgGroupId"], "z-last")
        self.assertEqual(block_comments[1]["svgGroupId"], "a-first")
        self.assertEqual(block_comments[2]["svgGroupId"], "m-middle")

    def test_extract_svg_group_ids_returns_references(self):
        """Test that returned block_comments are references to original objects"""
        original_comment = {"svgGroupId": "test-id", "text": "Original"}
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {"blockHeader": "", "blockComments": [original_comment]}
                ]
            }
        }

        _, block_comments = extract_svg_group_ids(entry)

        # Modify the returned comment
        block_comments[0]["text"] = "Modified"

        # Original should also be modified (same object reference)
        self.assertEqual(original_comment["text"], "Modified")


@pytest.mark.unit
class TestHasClassToken(unittest.TestCase):
    """Test cases for has_class_token function"""

    def test_has_class_token_with_exact_match(self):
        """Test that returns True for exact class match"""
        self.assertTrue(has_class_token("tkk", "tkk"))

    def test_has_class_token_with_multiple_classes(self):
        """Test that returns True when the wanted class is among multiple classes"""
        self.assertTrue(has_class_token("active tkk selected", "tkk"))
        self.assertTrue(has_class_token("selected tkk", "tkk"))
        self.assertTrue(has_class_token("tkk selected", "tkk"))

    def test_has_class_token_with_case_insensitive(self):
        """Test that class matching is case-insensitive"""
        self.assertTrue(has_class_token("TKK important", "tkk"))
        self.assertTrue(has_class_token("tkk", "TKK"))

    def test_has_class_token_not_present(self):
        """Test that returns False when the wanted class is not present"""
        self.assertFalse(has_class_token("active selected", "tkk"))
        self.assertFalse(has_class_token("", "tkk"))

    def test_has_class_token_with_empty_wanted_class(self):
        """Test that returns False when the wanted class is empty or whitespace"""
        self.assertFalse(has_class_token("tkk", ""))
        self.assertFalse(has_class_token("", ""))

    def test_has_class_token_with_spaces_and_strip(self):
        """Test that leading/trailing spaces in wanted class are stripped"""
        self.assertTrue(has_class_token("  tkk  ", "tkk"))
        self.assertTrue(has_class_token("active   tkk   selected", "tkk"))


if __name__ == '__main__':
    unittest.main()
