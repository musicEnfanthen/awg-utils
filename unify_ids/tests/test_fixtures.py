#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared test fixtures for unify_tkk_ids test suite

This module contains common test data structures and fixtures used across
multiple test files to reduce code duplication and improve maintainability.

Test Data Categories:
- JSON textcritics data structures
- SVG content examples
- Common test configurations

Usage:
    from tests.test_fixtures import SAMPLE_TEXTCRITIC_BASIC, SAMPLE_SVG
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _create_textcritic_entry(m_id, svg_group_ids, preamble="", block_header=""):
    """
    Helper function to create textcritic entries with consistent structure

    Args:
        m_id: The M identifier (e.g., "M_142")
        svg_group_ids: List of svgGroupId values
        preamble: Optional preamble text
        block_header: Optional block header text

    Returns:
        Dictionary representing a textcritic entry
    """
    return {
        "id": m_id,
        "commentary": {
            "preamble": preamble,
            "comments": [
                {
                    "blockHeader": block_header,
                    "blockComments": [
                        {"svgGroupId": svg_id} for svg_id in svg_group_ids
                    ]
                }
            ]
        }
    }


def _create_json_data(textcritic_entries):
    """
    Helper function to create complete JSON data structure

    Args:
        textcritic_entries: List of textcritic entry dictionaries

    Returns:
        Complete JSON data structure with textcritics array
    """
    return {"textcritics": textcritic_entries}


# =============================================================================
# INDIVIDUAL TEXTCRITIC SAMPLES
# =============================================================================

# Basic textcritic entry with valid awg-tkk prefixed IDs
SAMPLE_TEXTCRITICS_WITH_SINGLE_PREFIXED_ID = _create_textcritic_entry(
    "M_142_Sk1", ["awg-tkk-m142_sk1-001"]
)
SAMPLE_TEXTCRITICS_WITH_2_PREFIXED_IDS = _create_textcritic_entry(
    "M_142_Sk1", ["awg-tkk-m142_sk1-001", "awg-tkk-m142_sk1-002"]
)
SAMPLE_TEXTCRITICS_WITH_4_PREFIXED_IDS = _create_textcritic_entry(
    "M_142_Sk1", ["awg-tkk-m142_sk1-001", "awg-tkk-m142_sk1-002", "awg-tkk-m142_sk1-003", "awg-tkk-m142_sk1-004"]
)

# Textcritic entry with single unprefixed ID
SAMPLE_TEXTCRITICS_WITH_MIXED_IDS = _create_textcritic_entry(
    "M_145_TF1", ["old-id-1", "awg-tkk-m145_tf1-001"]
)

# Textcritic entry with multiple mixed IDs (some prefixed, some old/unprefixed)
SAMPLE_TEXTCRITICS_WITH_MULTIPLE_MIXED_IDS = _create_textcritic_entry(
    "M_150_Sk2_1", ["awg-tkk-m150_sk2_1-001", "old-id-2", "old-id-3", "awg-tkk-m150_sk2_1-002"]
)

# Textcritic entry with TODO svgGroupId (should be ignored)
SAMPLE_TEXTCRITICS_WITH_TODO = _create_textcritic_entry(
    "M_146_TF2", ["TODO", "awg-tkk-m146_tf2-001"]
)
SAMPLE_TEXTCRITICS_WITH_TODO_AND_MIXED_IDS = _create_textcritic_entry(
    "M_146_TF2", ["TODO", "awg-tkk-m146_tf2-001", "old-id-1"]
)

# Integration test samples (matches test_unify_tkk_ids.py structure)
SAMPLE_TEXTCRITICS_M143 = _create_textcritic_entry(
    "M_143", ["old-id-1", "old-id-2"]
)
SAMPLE_TEXTCRITICS_WITH_SKRT = _create_textcritic_entry(
    "M_144_SkRT", ["skrt-old-1"]
)
SAMPLE_TEXTCRITICS_SECOND = _create_textcritic_entry(
    "M_144_SkRT", ["old-id-3", "old-id-4"]
)


# =============================================================================
# COMPLETE JSON DATA STRUCTURES
# =============================================================================

# Single entry JSON structures
JSON_DATA_WITH_SINGLE_PREFIXED_ID = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_SINGLE_PREFIXED_ID]
)
JSON_DATA_WITH_2_PREFIXED_IDS = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_2_PREFIXED_IDS]
)
JSON_DATA_WITH_4_PREFIXED_IDS = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_4_PREFIXED_IDS]
)
JSON_DATA_WITH_MIXED_IDS = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_MIXED_IDS]
)
JSON_DATA_WITH_MULTIPLE_MIXED_IDS = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_MULTIPLE_MIXED_IDS]
)
JSON_DATA_WITH_TODO = _create_json_data([SAMPLE_TEXTCRITICS_WITH_TODO])
JSON_DATA_WITH_TODO_AND_MIXED_IDS = _create_json_data(
    [SAMPLE_TEXTCRITICS_WITH_TODO_AND_MIXED_IDS]
)
# Multi-entry JSON structures
JSON_DATA_INTEGRATION = _create_json_data(
    [SAMPLE_TEXTCRITICS_M143, SAMPLE_TEXTCRITICS_WITH_SKRT]
)
JSON_DATA_MULTIPLE_ENTRIES = _create_json_data([
    SAMPLE_TEXTCRITICS_WITH_MULTIPLE_MIXED_IDS,
    SAMPLE_TEXTCRITICS_SECOND
])

# Special case JSON structures
JSON_DATA_EMPTY = {"textcritics": []}

JSON_DATA_MALFORMED = {
    "textcritics": [
        {
            # Missing commentary structure
            "id": "M147"
        },
        {
            "id": "M148",
            "commentary": {
                # Missing comments
            }
        }
    ]
}


# =============================================================================
# SVG CONTENT SAMPLES
# =============================================================================

# Single SVG file with prefixed awg-tkk ID
SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID = {
    "test.svg": {
        "content": '<g class="tkk" id="awg-tkk-m142_sk1-001">content</g>'
    }
}

# Single SVG file with old/unprefixed ID
SAMPLE_SVG_WITH_SINGLE_UNPREFIXED_ID = {
    "test.svg": {
        "content": '<g class="tkk" id="old-id-1">content</g>'
    }
}

# Single SVG file with multiple prefixed awg-tkk IDs
SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS = {
    "test1.svg": {
        "content": (
            '<g class="tkk" id="awg-tkk-m142_sk1-001">content</g>'
            '<g class="tkk" id="awg-tkk-m142_sk2-002">content</g>'
        )
    },
}

# Single SVG file with multiple old/unprefixed IDs
SAMPLE_SVG_WITH_MULTIPLE_UNPREFIXED_IDS = {
    "test.svg": {
        "content": (
            '<g class="tkk" id="old-id-1">content</g>'
            '<g class="tkk" id="old-id-2">content</g>'
        )
    }
}

# Single SVG file with mixed prefixed and old IDs
SAMPLE_SVG_WITH_MIXED_IDS = {
    "test.svg": {
        "content": (
            '<g class="tkk" id="old-id-1">content</g>'
            '<g class="tkk" id="awg-tkk-m142_sk1-001">content</g>'
        )
    }
}

# Multiple SVG files with prefixed IDs
SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS = {
    "test1.svg": {
        "content": (
            '<g class="tkk" id="awg-tkk-m142_sk1-001">content</g>'
            '<g class="tkk" id="awg-tkk-m142_sk2-002">content</g>'
        )
    },
    "test2.svg": {
        "content": (
            '<g class="tkk" id="awg-tkk-m142_sk3-003">content</g>'
            '<g class="tkk" id="awg-tkk-m142_sk4-004">content</g>'
        )
    }
}

# Multiple SVG files with old/unprefixed IDs
SAMPLE_MULTIPLE_SVG_WITH_UNPREFIXED_IDS = {
    "test1.svg": {
        "content": (
            '<g class="tkk" id="old-id-1">content</g>'
            '<g class="tkk" id="old-id-2">content</g>'
        )
    },
    "test2.svg": {
        "content": (
            '<g class="tkk" id="old-id-3">content</g>'
            '<g class="tkk" id="old-id-4">content</g>'
        )
    }
}

# Multiple SVG files with mixed prefixed and old IDs
SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS = {
    "test1.svg": {
        "content": (
            '<g class="tkk" id="awg-tkk-m142_sk1-001">content</g>'
            '<g class="tkk" id="old-id-2">content</g>'
        )
    },
    "test2.svg": {
        "content": (
            '<g class="tkk" id="old-id-3">content</g>'
            '<g class="tkk" id="awg-tkk-m142_sk2-002">content</g>'
        )
    }
}
