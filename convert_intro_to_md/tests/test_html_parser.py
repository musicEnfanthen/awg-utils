"""Tests for utils/html_parser.py"""

from unittest.mock import patch

from bs4 import BeautifulSoup, NavigableString

from utils.html_parser import (
    _convert_a,
    _convert_blockquote,
    _convert_children,
    _convert_crossref,
    _convert_list,
    _convert_node,
    _convert_note_p,
    _convert_sup,
    _convert_table,
    _parse_block_content,
    _parse_block_notes,
    _parse_fragment,
    _parse_note,
    parse_intro,
)
from utils.nodes import (
    Block,
    Blockquote,
    CrossRef,
    FootnoteRef,
    ListBlock,
    ListItem,
    Note,
    Paragraph,
    Ref,
    Superscript,
    Table,
    Text,
)


class TestParseIntro:
    """Tests for the parse_intro function."""

    def test_empty_content_returns_empty_list(self):
        """Test that an intro with no content produces an empty list."""
        assert not parse_intro({})

    def test_returns_one_block_per_content_entry(self):
        """Test that one Block is produced for each entry in the content array."""
        intro = {"content": [{"blockId": "a"}, {"blockId": "b"}]}
        with (
            patch("utils.html_parser._parse_block_content", return_value=[]),
            patch("utils.html_parser._parse_block_notes", return_value=[]),
        ):
            result = parse_intro(intro)
        assert len(result) == 2
        assert all(isinstance(b, Block) for b in result)

    def test_block_id_is_forwarded(self):
        """Test that the blockId value becomes the Block id."""
        intro = {"content": [{"blockId": "op10-1"}]}
        with (
            patch("utils.html_parser._parse_block_content", return_value=[]),
            patch("utils.html_parser._parse_block_notes", return_value=[]),
        ):
            result = parse_intro(intro)
        assert result[0].id == "op10-1"

    def test_heading_is_none_when_no_block_header(self):
        """Test that a missing blockHeader produces heading=None."""
        intro = {"content": [{"blockId": "x"}]}
        with (
            patch("utils.html_parser._parse_block_content", return_value=[]),
            patch("utils.html_parser._parse_block_notes", return_value=[]),
        ):
            result = parse_intro(intro)
        assert result[0].heading is None

    def test_heading_parsed_when_block_header_present(self):
        """Test that a blockHeader string is parsed via _parse_fragment."""
        intro = {"content": [{"blockId": "x", "blockHeader": "<b>Title</b>"}]}
        sentinel = [Text(value="Title")]
        with (
            patch("utils.html_parser._parse_fragment", return_value=sentinel) as mock,
            patch("utils.html_parser._parse_block_content", return_value=[]),
            patch("utils.html_parser._parse_block_notes", return_value=[]),
        ):
            result = parse_intro(intro)
        mock.assert_called_once_with("<b>Title</b>")
        assert result[0].heading is sentinel

    def test_content_delegated_to_parse_block_content(self):
        """Test that blockContent is passed to _parse_block_content."""
        block_content = ["<p>text</p>"]
        intro = {"content": [{"blockId": "x", "blockContent": block_content}]}
        sentinel = [Text(value="text")]
        with (
            patch(
                "utils.html_parser._parse_block_content", return_value=sentinel
            ) as mock,
            patch("utils.html_parser._parse_block_notes", return_value=[]),
        ):
            result = parse_intro(intro)
        mock.assert_called_once_with(block_content)
        assert result[0].content is sentinel

    def test_notes_delegated_to_parse_block_notes(self):
        """Test that blockNotes is passed to _parse_block_notes."""
        block_notes = ['<p id="n-1">note</p>']
        intro = {"content": [{"blockId": "x", "blockNotes": block_notes}]}
        note = Note(id="n-1", children=[])
        with (
            patch("utils.html_parser._parse_block_content", return_value=[]),
            patch("utils.html_parser._parse_block_notes", return_value=[note]) as mock,
        ):
            result = parse_intro(intro)
        mock.assert_called_once_with(block_notes)
        assert result[0].notes == [note]

    def test_multiple_blocks_with_all_fields_are_assembled_correctly(self):
        """Test that each block's id, heading, content, and notes are assembled correctly."""
        heading_a = [Text(value="Heading A")]
        heading_b = [Text(value="Heading B")]
        content_a = [Paragraph(children=[])]
        content_b = [Paragraph(children=[])]
        note_a = Note(id="n-a", children=[])
        note_b = Note(id="n-b", children=[])
        intro = {
            "content": [
                {
                    "blockId": "block-a",
                    "blockHeader": "A",
                    "blockContent": ["ca"],
                    "blockNotes": ["na"],
                },
                {
                    "blockId": "block-b",
                    "blockHeader": "B",
                    "blockContent": ["cb"],
                    "blockNotes": ["nb"],
                },
            ]
        }
        with (
            patch(
                "utils.html_parser._parse_fragment",
                side_effect=[heading_a, heading_b],
            ),
            patch(
                "utils.html_parser._parse_block_content",
                side_effect=[content_a, content_b],
            ),
            patch(
                "utils.html_parser._parse_block_notes",
                side_effect=[[note_a], [note_b]],
            ),
        ):
            result = parse_intro(intro)
        assert result[0].id == "block-a"
        assert result[0].heading is heading_a
        assert result[0].content is content_a
        assert result[0].notes == [note_a]
        assert result[1].id == "block-b"
        assert result[1].heading is heading_b
        assert result[1].content is content_b
        assert result[1].notes == [note_b]


class TestParseBlockContent:
    """Tests for the _parse_block_content function."""

    def test_empty_list_returns_empty_list(self):
        """Test that an empty input list produces an empty list."""
        assert not _parse_block_content([])

    def test_delegates_each_item_to_parse_fragment(self):
        """Test that each HTML string is passed to _parse_fragment."""
        with patch("utils.html_parser._parse_fragment", return_value=[]) as mock:
            _parse_block_content(["<p>a</p>", "<p>b</p>"])
        assert mock.call_count == 2

    def test_results_from_parse_fragment_are_concatenated(self):
        """Test that nodes returned by _parse_fragment for each item are concatenated."""
        a = Text(value="a")
        b = Text(value="b")
        with patch("utils.html_parser._parse_fragment", side_effect=[[a], [b]]):
            result = _parse_block_content(["<p>a</p>", "<p>b</p>"])
        assert result == [a, b]


class TestParseFragment:
    """Tests for the _parse_fragment function."""

    def test_empty_string_returns_empty_list(self):
        """Test that an empty fragment returns an empty list."""
        assert not _parse_fragment("")

    def test_plain_text_returns_text_node(self):
        """Test that a plain text fragment produces a single Text node."""
        result = _parse_fragment("hello")
        assert len(result) == 1
        assert isinstance(result[0], Text)
        assert result[0].value == "hello"

    def test_delegates_top_level_children_to_convert_node(self):
        """Test that each top-level node in the soup is passed to _convert_node."""
        with patch("utils.html_parser._convert_node", return_value=[]) as mock:
            _parse_fragment("<p>a</p><p>b</p>")
        assert mock.call_count == 2

    def test_results_from_convert_node_are_concatenated(self):
        """Test that nodes returned by _convert_node for each child are concatenated."""
        a = Text(value="a")
        b = Text(value="b")
        with patch("utils.html_parser._convert_node", side_effect=[[a], [b]]):
            result = _parse_fragment("<p>a</p><p>b</p>")
        assert result == [a, b]


class TestParseBlockNotes:
    """Tests for the _parse_block_notes function."""

    def test_empty_list_returns_empty_list(self):
        """Test that an empty input list produces an empty list."""
        assert not _parse_block_notes([])

    def test_delegates_each_item_to_parse_note(self):
        """Test that each HTML string in the input is passed to _parse_note."""
        html_items = ['<p id="n-1">a</p>', '<p id="n-2">b</p>']
        with patch("utils.html_parser._parse_note", return_value=None) as mock:
            _parse_block_notes(html_items)
        assert mock.call_count == 2

    def test_valid_notes_are_collected(self):
        """Test that Note objects returned by _parse_note are included in the result."""
        note_a = Note(id="n-1", children=[])
        note_b = Note(id="n-2", children=[])
        with patch("utils.html_parser._parse_note", side_effect=[note_a, note_b]):
            result = _parse_block_notes(["a", "b"])
        assert result == [note_a, note_b]

    def test_none_results_from_parse_note_are_dropped(self):
        """Test that None values returned by _parse_note are excluded from the result."""
        note = Note(id="n-1", children=[])
        with patch("utils.html_parser._parse_note", side_effect=[None, note, None]):
            result = _parse_block_notes(["a", "b", "c"])
        assert result == [note]


class TestParseNote:
    """Tests for the _parse_note function."""

    def test_returns_note_for_valid_input(self):
        """Test that a well-formed note paragraph produces a Note node."""
        html = '<p id="note-1">text</p>'
        assert isinstance(_parse_note(html), Note)

    def test_note_id_is_forwarded(self):
        """Test that the id attribute of the <p> becomes the Note id."""
        html = '<p id="note-3">text</p>'
        assert _parse_note(html).id == "note-3"

    def test_delegates_to_convert_note_p(self):
        """Test that conversion is delegated to _convert_note_p."""
        html = '<p id="note-1">text</p>'
        sentinel = Note(id="note-1", children=[])
        with patch("utils.html_parser._convert_note_p", return_value=sentinel) as mock:
            result = _parse_note(html)
        assert mock.call_count == 1
        assert result is sentinel

    def test_no_p_tag_returns_none(self):
        """Test that HTML without a <p> tag returns None."""
        assert _parse_note("<span>no paragraph</span>") is None

    def test_p_without_id_returns_none(self):
        """Test that a <p> tag with no id attribute returns None."""
        assert _parse_note("<p>no id</p>") is None


class TestConvertNode:
    """Tests for the _convert_node function."""

    def test_navigable_string_returns_text_node(self):
        """Test that a NavigableString produces a Text node with the string value."""
        result = _convert_node(NavigableString("hello"))
        assert len(result) == 1
        assert isinstance(result[0], Text)
        assert result[0].value == "hello"

    def test_non_tag_non_string_returns_empty_list(self):
        """Test that a non-Tag, non-NavigableString input produces an empty list."""
        assert not _convert_node(object())

    def test_simple_tag_returns_single_wrapper_node(self):
        """Test that a simple tag like <p> produces a single node of the mapped type."""
        tag = _tag("<p>text</p>")
        result = _convert_node(tag)
        assert len(result) == 1
        assert isinstance(result[0], Paragraph)

    def test_simple_tag_delegates_children_to_convert_children(self):
        """Test that a simple tag passes itself to _convert_children for child conversion."""
        tag = _tag("<p>text</p>")
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result[0].children is sentinel

    def test_a_tag_delegates_to_convert_a(self):
        """Test that an <a> tag dispatches to _convert_a."""
        tag = _tag('<a href="/x">link</a>')
        sentinel = [Text(value="sentinel")]
        with patch("utils.html_parser._convert_a", return_value=sentinel) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_awg_crossref_tag_delegates_to_convert_crossref(self):
        """Test that an <awg-crossref> tag dispatches to _convert_crossref."""
        tag = _tag('<awg-crossref n="3"></awg-crossref>')
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_crossref", return_value=sentinel
        ) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_blockquote_tag_delegates_to_convert_blockquote(self):
        """Test that a <blockquote> tag dispatches to _convert_blockquote."""
        tag = _tag("<blockquote><p>q</p></blockquote>")
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_blockquote", return_value=sentinel
        ) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_sup_tag_delegates_to_convert_sup(self):
        """Test that a <sup> tag dispatches to _convert_sup."""
        tag = _tag("<sup>2</sup>")
        sentinel = [Text(value="sentinel")]
        with patch("utils.html_parser._convert_sup", return_value=sentinel) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_table_tag_delegates_to_convert_table(self):
        """Test that a <table> tag dispatches to _convert_table and wraps the result."""
        tag = _tag("<table><tr><td>x</td></tr></table>")
        table_node = Table()
        with patch("utils.html_parser._convert_table", return_value=table_node) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result == [table_node]

    def test_ul_tag_delegates_to_convert_list(self):
        """Test that a <ul> tag dispatches to _convert_list."""
        tag = _tag("<ul><li>a</li></ul>")
        sentinel = [Text(value="sentinel")]
        with patch("utils.html_parser._convert_list", return_value=sentinel) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_unknown_tag_is_transparent(self):
        """Test that an unknown tag delegates directly to _convert_children."""
        tag = _tag("<div>text</div>")
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_node(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel


class TestConvertChildren:
    """Tests for the _convert_children function."""

    def test_empty_tag_returns_empty_list(self):
        """Test that a tag with no children returns an empty list."""
        tag = _tag("<div></div>")
        assert not _convert_children(tag)

    def test_delegates_each_child_to_convert_node(self):
        """Test that each child of the tag is passed to _convert_node."""
        tag = _tag("<p>a<b>b</b></p>")
        with patch("utils.html_parser._convert_node", return_value=[]) as mock:
            _convert_children(tag)
        assert mock.call_count == 2

    def test_results_from_all_children_are_concatenated(self):
        """Test that results returned by _convert_node for each child are concatenated."""
        tag = _tag("<p>a<b>b</b></p>")
        a = Text(value="a")
        b = Text(value="b")
        with patch("utils.html_parser._convert_node", side_effect=[[a], [b]]):
            result = _convert_children(tag)
        assert result == [a, b]

    def test_navigable_string_child_produces_text_node(self):
        """Test that a plain text child yields a Text node with the correct value."""
        tag = _tag("<p>hello</p>")
        result = _convert_children(tag)
        assert len(result) == 1
        assert isinstance(result[0], Text)
        assert result[0].value == "hello"


def _tag(html: str):
    """Parse *html* and return the first child tag."""
    return BeautifulSoup(html, "html.parser").find()


class TestConvertA:
    """Tests for the _convert_a function."""

    def test_with_href_returns_ref_node(self):
        """Test that an anchor with href produces a Ref node."""
        tag = _tag('<a href="/foo">text</a>')
        result = _convert_a(tag)
        assert len(result) == 1
        assert isinstance(result[0], Ref)

    def test_with_href_passes_href_as_target(self):
        """Test that the href value is forwarded as the Ref target."""
        tag = _tag('<a href="/foo">text</a>')
        result = _convert_a(tag)
        assert result[0].target == "/foo"

    def test_with_href_delegates_children_to_convert_children(self):
        """Test that children of an href anchor are produced by _convert_children."""
        tag = _tag('<a href="/foo">text</a>')
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_a(tag)
        mock.assert_called_once_with(tag)
        assert result[0].children is sentinel

    def test_without_href_delegates_to_convert_children(self):
        """Test that an anchor without href is transparent and delegates to _convert_children."""
        tag = _tag("<a>text</a>")
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_a(tag)
        mock.assert_called_once_with(tag)
        assert result is sentinel

    def test_without_href_returns_children_directly(self):
        """Test that a no-href anchor is transparent — no Ref wrapper is added."""
        tag = _tag("<a>text</a>")
        result = _convert_a(tag)
        assert not any(isinstance(n, Ref) for n in result)


class TestConvertBlockquote:
    """Tests for the _convert_blockquote function."""

    def test_returns_single_blockquote_node(self):
        """Test that the result is a single Blockquote node."""
        tag = _tag("<blockquote><p>text</p></blockquote>")
        result = _convert_blockquote(tag)
        assert len(result) == 1
        assert isinstance(result[0], Blockquote)

    def test_delegates_to_convert_children(self):
        """Test that child conversion is delegated to _convert_children."""
        tag = _tag("<blockquote><p>text</p></blockquote>")
        sentinel = [Paragraph(children=[])]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            _convert_blockquote(tag)
        mock.assert_called_once_with(tag)

    def test_paragraphs_from_children_become_blockquote_paragraphs(self):
        """Test that Paragraph nodes returned by _convert_children are passed to Blockquote."""
        tag = _tag("<blockquote><p>text</p></blockquote>")
        para = Paragraph(children=[])
        with patch("utils.html_parser._convert_children", return_value=[para]):
            result = _convert_blockquote(tag)
        assert result[0].paragraphs == [para]

    def test_non_paragraph_children_are_filtered_out(self):
        """Test that non-Paragraph nodes returned by _convert_children are dropped."""
        tag = _tag("<blockquote><p>text</p></blockquote>")
        non_para = Text(value="noise")
        with patch("utils.html_parser._convert_children", return_value=[non_para]):
            result = _convert_blockquote(tag)
        assert not result[0].paragraphs


class TestConvertCrossref:
    """Tests for the _convert_crossref function."""

    def test_valid_n_returns_crossref_node(self):
        """Test that a numeric n attribute produces a CrossRef node."""
        tag = _tag('<awg-crossref n="3"/>')
        result = _convert_crossref(tag)
        assert len(result) == 1
        assert isinstance(result[0], CrossRef)

    def test_valid_n_value_is_forwarded(self):
        """Test that the integer value of n is set on the CrossRef node."""
        tag = _tag('<awg-crossref n="7"/>')
        result = _convert_crossref(tag)
        assert result[0].n == 7

    def test_missing_n_returns_empty_list(self):
        """Test that a missing n attribute returns an empty list."""
        tag = _tag("<awg-crossref/>")
        assert not _convert_crossref(tag)

    def test_non_numeric_n_returns_empty_list(self):
        """Test that a non-numeric n attribute returns an empty list."""
        tag = _tag('<awg-crossref n="abc"/>')
        assert not _convert_crossref(tag)


class TestConvertList:
    """Tests for the _convert_list function."""

    def test_ul_returns_single_listblock_node(self):
        """Test that a <ul> produces a single ListBlock node."""
        tag = _tag("<ul><li>a</li></ul>")
        result = _convert_list(tag)
        assert len(result) == 1
        assert isinstance(result[0], ListBlock)

    def test_ul_is_unordered(self):
        """Test that a <ul> tag produces an unordered ListBlock."""
        tag = _tag("<ul><li>a</li></ul>")
        assert not _convert_list(tag)[0].ordered

    def test_ol_is_ordered(self):
        """Test that an <ol> tag produces an ordered ListBlock."""
        tag = _tag("<ol><li>a</li></ol>")
        assert _convert_list(tag)[0].ordered

    def test_delegates_to_convert_children(self):
        """Test that child conversion is delegated to _convert_children."""
        tag = _tag("<ul><li>a</li></ul>")
        sentinel = [ListItem(children=[])]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            _convert_list(tag)
        mock.assert_called_once_with(tag)

    def test_list_items_from_children_become_items(self):
        """Test that ListItem nodes returned by _convert_children are passed to ListBlock."""
        tag = _tag("<ul><li>a</li></ul>")
        item = ListItem(children=[])
        with patch("utils.html_parser._convert_children", return_value=[item]):
            result = _convert_list(tag)
        assert result[0].items == [item]

    def test_non_list_item_children_are_filtered_out(self):
        """Test that non-ListItem nodes returned by _convert_children are dropped."""
        tag = _tag("<ul><li>a</li></ul>")
        with patch(
            "utils.html_parser._convert_children", return_value=[Text(value="noise")]
        ):
            result = _convert_list(tag)
        assert not result[0].items


class TestConvertNoteP:
    """Tests for the _convert_note_p function."""

    def test_returns_note_node(self):
        """Test that the result is a Note node."""
        p = _tag('<p id="note-1">text</p>')
        assert isinstance(_convert_note_p(p, "note-1"), Note)

    def test_note_id_is_forwarded(self):
        """Test that the note_id argument is set as the id on the Note."""
        p = _tag('<p id="note-3">text</p>')
        assert _convert_note_p(p, "note-3").id == "note-3"

    def test_delegates_children_to_convert_children(self):
        """Test that the remaining children of p are passed to _convert_children."""
        p = _tag('<p id="note-1">text</p>')
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_note_p(p, "note-1")
        mock.assert_called_once_with(p)
        assert result.children is sentinel

    def test_children_from_convert_children_become_note_children(self):
        """Test that nodes returned by _convert_children become the Note's children."""
        p = _tag('<p id="note-1">text</p>')
        child = Text(value="body")
        with patch("utils.html_parser._convert_children", return_value=[child]):
            result = _convert_note_p(p, "note-1")
        assert result.children == [child]

    def test_backlink_anchor_is_removed(self):
        """Test that a <a class="note-backlink"> element is stripped from the note content."""
        p = _tag('<p id="n-1"><a class="note-backlink">↑</a>remaining</p>')
        result = _convert_note_p(p, "n-1")
        text_values = [c.value for c in result.children if isinstance(c, Text)]
        assert "↑" not in text_values
        assert "remaining" in text_values

    def test_pipe_separator_prefix_is_stripped(self):
        """Test that a leading ' | ' in the first text node is removed."""
        p = _tag('<p id="n-1"> | note text</p>')
        result = _convert_note_p(p, "n-1")
        assert result.children[0].value == "note text"


class TestConvertSup:
    """Tests for the _convert_sup function."""

    def test_note_ref_anchor_returns_footnote_ref(self):
        """Test that a <sup> with a note-ref anchor produces a FootnoteRef node."""
        tag = _tag('<sup><a id="note-ref-3">3</a></sup>')
        with patch(
            "utils.html_parser.ReplacementUtils.parse_note_ref_id", return_value=3
        ):
            result = _convert_sup(tag)
        assert len(result) == 1
        assert isinstance(result[0], FootnoteRef)

    def test_footnote_ref_n_value_is_forwarded(self):
        """Test that the value returned by parse_note_ref_id is set as FootnoteRef.n."""
        tag = _tag('<sup><a id="note-ref-5">5</a></sup>')
        with patch(
            "utils.html_parser.ReplacementUtils.parse_note_ref_id", return_value=5
        ):
            result = _convert_sup(tag)
        assert result[0].n == 5

    def test_no_matching_anchor_returns_superscript(self):
        """Test that a <sup> without a note-ref anchor produces a Superscript node."""
        tag = _tag("<sup>2</sup>")
        with patch(
            "utils.html_parser.ReplacementUtils.parse_note_ref_id", return_value=None
        ):
            result = _convert_sup(tag)
        assert len(result) == 1
        assert isinstance(result[0], Superscript)

    def test_superscript_delegates_children_to_convert_children(self):
        """Test that the Superscript path delegates children to _convert_children."""
        tag = _tag("<sup>2</sup>")
        sentinel = [Text(value="sentinel")]
        with (
            patch(
                "utils.html_parser.ReplacementUtils.parse_note_ref_id",
                return_value=None,
            ),
            patch("utils.html_parser._convert_children", return_value=sentinel) as mock,
        ):
            result = _convert_sup(tag)
        mock.assert_called_once_with(tag)
        assert result[0].children is sentinel


class TestConvertTable:
    """Tests for the _convert_table function."""

    def test_returns_table_node(self):
        """Test that a <table> tag produces a Table node."""
        tag = _tag("<table><tr><td>x</td></tr></table>")
        assert isinstance(_convert_table(tag), Table)

    def test_rows_created_per_tr(self):
        """Test that one Row is created for each <tr> element."""
        tag = _tag("<table><tr><td>a</td></tr><tr><td>b</td></tr></table>")
        assert len(_convert_table(tag).rows) == 2

    def test_cell_children_delegated_to_convert_children(self):
        """Test that each cell's content is produced by _convert_children."""
        tag = _tag("<table><tr><td>x</td></tr></table>")
        sentinel = [Text(value="sentinel")]
        with patch(
            "utils.html_parser._convert_children", return_value=sentinel
        ) as mock:
            result = _convert_table(tag)
        mock.assert_called_once()
        assert result.rows[0].cells[0].children is sentinel

    def test_th_only_row_outside_thead_is_header(self):
        """Test that a <tr> with only <th> cells outside <thead> has is_header=True."""
        tag = _tag("<table><tr><th>Header</th></tr></table>")
        assert _convert_table(tag).rows[0].is_header is True

    def test_td_row_is_not_header(self):
        """Test that a <tr> with <td> cells has is_header=False."""
        tag = _tag("<table><tr><td>data</td></tr></table>")
        assert _convert_table(tag).rows[0].is_header is False

    def test_row_gap_class_sets_gap_before(self):
        """Test that a <tr class="row-gap"> produces a Row with gap_before=True."""
        tag = _tag('<table><tr class="row-gap"><td>x</td></tr></table>')
        assert _convert_table(tag).rows[0].gap_before is True

    def test_text_center_class_sets_text_center(self):
        """Test that a <tr class="text-center"> produces a Row with text_center=True."""
        tag = _tag('<table><tr class="text-center"><td>x</td></tr></table>')
        assert _convert_table(tag).rows[0].text_center is True

    def test_colspan_is_forwarded(self):
        """Test that the colspan attribute of a cell is forwarded as an integer."""
        tag = _tag('<table><tr><td colspan="3">x</td></tr></table>')
        assert _convert_table(tag).rows[0].cells[0].colspan == 3

    def test_indent_from_tab_class(self):
        """Test that a cell with class="tab" has indent=True."""
        tag = _tag('<table><tr><td class="tab">x</td></tr></table>')
        assert _convert_table(tag).rows[0].cells[0].indent is True
