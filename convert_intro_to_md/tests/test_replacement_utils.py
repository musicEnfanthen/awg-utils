"""Tests for utils/replacement_utils.py"""

from utils.replacement_utils import ReplacementUtils


class TestNormalizeWhitespace:
    """Tests for the normalize_whitespace function."""

    def test_replaces_non_breaking_space(self):
        """Test that non-breaking spaces are replaced with regular spaces."""
        assert ReplacementUtils.normalize_whitespace("a\xa0b") == "a b"

    def test_collapses_triple_newlines(self):
        """Test that three or more consecutive newlines are collapsed to two."""
        assert ReplacementUtils.normalize_whitespace("a\n\n\nb") == "a\n\nb"

    def test_collapses_many_newlines(self):
        """Test that a long run of newlines is collapsed to two."""
        assert ReplacementUtils.normalize_whitespace("a\n\n\n\n\nb") == "a\n\nb"

    def test_preserves_double_newlines(self):
        """Test that exactly two consecutive newlines are left unchanged."""
        assert ReplacementUtils.normalize_whitespace("a\n\nb") == "a\n\nb"

    def test_strips_leading_and_trailing_whitespace(self):
        """Test that leading and trailing whitespace is stripped."""
        assert ReplacementUtils.normalize_whitespace("  hello  ") == "hello"

    def test_plain_text_unchanged(self):
        """Test that plain text with no special whitespace is returned unchanged."""
        assert ReplacementUtils.normalize_whitespace("plain text") == "plain text"


class TestParseNoteRefId:
    """Tests for the parse_note_ref_id function."""

    def test_returns_note_number_for_valid_id(self):
        """Test that a valid note-ref id returns its integer note number."""
        assert ReplacementUtils.parse_note_ref_id("note-ref-1") == 1

    def test_returns_note_number_for_larger_n(self):
        """Test that a valid note-ref id with a multi-digit number is parsed correctly."""
        assert ReplacementUtils.parse_note_ref_id("note-ref-42") == 42

    def test_returns_none_for_non_matching_string(self):
        """Test that a string not matching the pattern returns None."""
        assert ReplacementUtils.parse_note_ref_id("note-1") is None

    def test_returns_none_for_empty_string(self):
        """Test that an empty string returns None."""
        assert ReplacementUtils.parse_note_ref_id("") is None

    def test_returns_none_for_partial_match(self):
        """Test that a string with extra characters returns None."""
        assert ReplacementUtils.parse_note_ref_id("note-ref-1-extra") is None


class TestReplaceCrossrefs:
    """Tests for the replace_crossrefs function."""

    def test_replaces_crossref_anchor(self):
        """Test that a cross-reference anchor is replaced by a synthetic tag."""
        html = "<a fragmentId: 'note-3'\">3</a>"
        result = ReplacementUtils.replace_crossrefs(html)
        assert result == '<awg-crossref n="3"/>'

    def test_replaces_multiple_crossref_anchors(self):
        """Test that multiple cross-reference anchors are all replaced."""
        html = (
            'See <a href="/" fragmentId: \'note-1\'">1</a>'
            ' and <a href="/" fragmentId: \'note-2\'">2</a>.'
        )
        result = ReplacementUtils.replace_crossrefs(html)
        assert '<awg-crossref n="1"/>' in result
        assert '<awg-crossref n="2"/>' in result

    def test_ignores_note_ref_anchors(self):
        """Test that anchors with id=\"note-ref-N\" are not replaced."""
        html = '<sup><a id="note-ref-1">1</a></sup>'
        assert ReplacementUtils.replace_crossrefs(html) == html

    def test_plain_text_unchanged(self):
        """Test that plain text without anchors is returned unchanged."""
        assert ReplacementUtils.replace_crossrefs("hello world") == "hello world"


class TestSeparateAdjacentTables:
    """Tests for the separate_adjacent_tables function."""

    def test_inserts_blank_line_between_adjacent_tables(self):
        """Test that a blank line is inserted between two back-to-back tables."""
        text = "| a | b |\n| - | - |\n\n| c | d |\n| - | - |"
        result = ReplacementUtils.separate_adjacent_tables(text)
        assert result == "| a | b |\n| - | - |\n\n\n| c | d |\n| - | - |"

    def test_inserts_blank_line_for_multiple_adjacent_pairs(self):
        """Test that a blank line is inserted for each adjacent table pair."""
        text = "| a |\n| - |\n\n| b |\n| - |\n\n| c |\n| - |"
        result = ReplacementUtils.separate_adjacent_tables(text)
        assert result == "| a |\n| - |\n\n\n| b |\n| - |\n\n\n| c |\n| - |"

    def test_no_change_when_already_separated(self):
        """Test that tables already separated by two blank lines are left unchanged."""
        text = "| a | b |\n| - | - |\n\n\n| c | d |\n| - | - |"
        assert ReplacementUtils.separate_adjacent_tables(text) == text

    def test_no_change_for_plain_text(self):
        """Test that plain text without tables is returned unchanged."""
        text = "paragraph one\n\nparagraph two"
        assert ReplacementUtils.separate_adjacent_tables(text) == text

    def test_no_change_for_single_table(self):
        """Test that a single table with no successor is returned unchanged."""
        text = "| a | b |\n| - | - |\n| 1 | 2 |"
        assert ReplacementUtils.separate_adjacent_tables(text) == text


class TestStripAngularBindings:
    """Tests for the strip_angular_bindings function."""

    def test_removes_click_binding(self):
        """Test that a (click)=\"...\" attribute is removed."""
        html = '<a (click)="doSomething()">link</a>'
        assert ReplacementUtils.strip_angular_bindings(html) == "<a>link</a>"

    def test_removes_multiple_bindings(self):
        """Test that multiple Angular bindings are all removed."""
        html = '<a (click)="a()" (mouseenter)="b()">x</a>'
        assert ReplacementUtils.strip_angular_bindings(html) == "<a>x</a>"

    def test_plain_html_unchanged(self):
        """Test that HTML without Angular bindings is returned unchanged."""
        html = '<a href="/foo">bar</a>'
        assert ReplacementUtils.strip_angular_bindings(html) == html

    def test_plain_text_unchanged(self):
        """Test that plain text is returned unchanged."""
        assert ReplacementUtils.strip_angular_bindings("hello") == "hello"
