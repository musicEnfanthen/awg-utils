"""Tests for utils/md_renderer.py"""

from unittest.mock import patch

from utils.md_renderer import _render_list
from utils.nodes import (
    ListBlock,
    ListItem,
    Text,
)


class TestRenderList:
    """Tests for the _render_list function."""

    def test_unordered_list_items_are_prefixed_with_dash(self):
        """Test that each unordered list item is rendered with a '- ' prefix."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="a")]),
                ListItem(children=[Text(value="b")]),
            ],
            ordered=False,
        )
        result = _render_list(node)
        assert result == "- a\n- b"

    def test_ordered_list_items_are_prefixed_with_number(self):
        """Test that each ordered list item is rendered with a '1. ', '2. ', ... prefix."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="first")]),
                ListItem(children=[Text(value="second")]),
            ],
            ordered=True,
        )
        result = _render_list(node)
        assert result == "1. first\n2. second"

    def test_list_items_are_joined_with_newline(self):
        """Test that list items are joined by newlines with no trailing newline."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="x")]),
                ListItem(children=[Text(value="y")]),
                ListItem(children=[Text(value="z")]),
            ],
            ordered=False,
        )
        result = _render_list(node)
        assert result.count("\n") == 2

    def test_list_item_children_rendered_via_render_inline_children(self):
        """Test that each item's children are passed to _render_inline_children."""
        sentinel = "RENDERED"
        node = ListBlock(
            items=[ListItem(children=[Text(value="x")])],
            ordered=False,
        )
        with patch(
            "utils.md_renderer._render_inline_children", return_value=sentinel
        ) as mock:
            result = _render_list(node)
        mock.assert_called_once()
        assert sentinel in result

    def test_empty_unordered_list_returns_empty_string(self):
        """Test that an unordered list with no items returns an empty string."""
        node = ListBlock(items=[], ordered=False)
        assert _render_list(node) == ""

    def test_empty_ordered_list_returns_empty_string(self):
        """Test that an ordered list with no items returns an empty string."""
        node = ListBlock(items=[], ordered=True)
        assert _render_list(node) == ""
