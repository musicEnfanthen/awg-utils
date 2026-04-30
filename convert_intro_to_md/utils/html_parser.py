"""Parse AWG intro JSON blocks into format-neutral IR nodes (see utils/nodes.py)."""

from bs4 import BeautifulSoup, NavigableString, Tag

from utils.replacement_utils import ReplacementUtils
from utils.nodes import (
    Block,
    Blockquote,
    Bold,
    Cell,
    CrossRef,
    FootnoteRef,
    Italic,
    ListBlock,
    ListItem,
    Node,
    Note,
    Paragraph,
    Ref,
    Row,
    Strikethrough,
    Superscript,
    Table,
    Text,
    Underline,
)

_SIMPLE_TAG_MAP: dict[str, type] = {
    "b": Bold,
    "em": Italic,
    "i": Italic,
    "li": ListItem,
    "p": Paragraph,
    "s": Strikethrough,
    "strong": Bold,
    "u": Underline,
}


def parse_intro(intro: dict) -> list[Block]:
    """Parse a single intro JSON object into a list of Block IR nodes.

    Args:
        intro (Dict): A single intro object from the JSON ``intro`` array.

    Returns:
        List[Block]: The parsed blocks in document order.
    """
    blocks = []
    for raw in intro.get("content", []):
        block_id = (raw.get("blockId") or "").strip()
        raw_heading = (raw.get("blockHeader") or "").strip()
        heading = _parse_fragment(raw_heading) if raw_heading else None
        content = _parse_block_content(raw.get("blockContent", []))
        notes = _parse_block_notes(raw.get("blockNotes", []))
        blocks.append(Block(id=block_id, heading=heading, content=content, notes=notes))
    return blocks


# ---------------------------------------------------------------------------
# Block-content and note parsing
# ---------------------------------------------------------------------------


def _parse_block_content(block_content: list[str]) -> list[Node]:
    """Parse a list of HTML fragment strings into IR nodes.

    Args:
        block_content (List[str]): Raw HTML fragment strings from ``blockContent``.

    Returns:
        List[Node]: The parsed IR nodes in document order.
    """
    nodes: list[Node] = []
    for html in block_content:
        nodes.extend(_parse_fragment(html))
    return nodes


def _parse_fragment(html: str) -> list[Node]:
    """Parse a single HTML fragment string into a list of IR nodes.

    Args:
        html (str): A raw HTML fragment string (may contain Angular bindings).

    Returns:
        List[Node]: The top-level IR nodes produced from the fragment.
    """
    soup = BeautifulSoup(_prepare_html(html), "html.parser")
    nodes: list[Node] = []
    for child in soup.children:
        nodes.extend(_convert_node(child))
    return nodes


def _parse_block_notes(block_notes: list[str]) -> list[Note]:
    """Parse a list of blockNote HTML strings into :class:`Note` IR nodes.

    Args:
        block_notes (List[str]): Raw blockNote HTML strings from ``blockNotes``.

    Returns:
        List[Note]: The successfully parsed notes in source order.
    """
    notes: list[Note] = []
    for note_html in block_notes:
        note = _parse_note(note_html)
        if note:
            notes.append(note)
    return notes


def _parse_note(note_html: str) -> Note | None:
    """Parse a single blockNote HTML string into a :class:`Note` IR node.

    Strips the backlink anchor and the ``" | "`` separator that follows it.

    Args:
        note_html (str): A raw blockNote HTML string.

    Returns:
        Note | None: The parsed note, or ``None`` if no note id was found.
    """
    soup = BeautifulSoup(_prepare_html(note_html), "html.parser")
    p = soup.find("p")
    if not p:
        return None
    note_id = p.get("id")
    if not note_id:
        return None
    return _convert_note_p(p, note_id)


# ---------------------------------------------------------------------------
# Node conversion
# ---------------------------------------------------------------------------


def _convert_node(bs_node) -> list[Node]:  # pylint: disable=too-many-return-statements
    """Recursively convert a BeautifulSoup node to a list of IR nodes.

    Transparent tags (``div``, ``span``, ``tbody``, unknown) pass their
    children through without wrapping.

    Args:
        bs_node: A BeautifulSoup :class:`~bs4.element.Tag` or
            :class:`~bs4.element.NavigableString`.

    Returns:
        List[Node]: Zero or more IR nodes.
    """
    if isinstance(bs_node, NavigableString):
        return [Text(value=str(bs_node))]
    if not isinstance(bs_node, Tag):
        return []

    tag = bs_node.name

    if tag in _SIMPLE_TAG_MAP:
        return [_SIMPLE_TAG_MAP[tag](children=_convert_children(bs_node))]
    if tag == "a":
        return _convert_a(bs_node)
    if tag == "awg-crossref":
        return _convert_crossref(bs_node)
    if tag == "blockquote":
        return _convert_blockquote(bs_node)
    if tag == "sup":
        return _convert_sup(bs_node)
    if tag == "table":
        return [_convert_table(bs_node)]
    if tag in ("ul", "ol"):
        return _convert_list(bs_node)
    # tbody is transparent; also div, span, and unknown tags
    return _convert_children(bs_node)


def _convert_children(bs_node: Tag) -> list[Node]:
    """Convert all children of a BeautifulSoup tag to IR nodes.

    Args:
        bs_node (Tag): The parent BeautifulSoup tag.

    Returns:
        List[Node]: The concatenated IR nodes from all children.
    """
    nodes: list[Node] = []
    for child in bs_node.children:
        nodes.extend(_convert_node(child))
    return nodes


def _convert_a(tag: Tag) -> list[Node]:
    """Convert an ``<a>`` tag to a :class:`Ref` node or transparent children.

    If the anchor has an ``href`` attribute it becomes a :class:`Ref`; otherwise
    (e.g. Angular-only anchors) it is transparent and its children are returned
    directly.

    Args:
        tag (Tag): The ``<a>`` BeautifulSoup tag.

    Returns:
        List[Node]: A :class:`Ref` node, or the children of the anchor.
    """
    href = tag.get("href")
    if href:
        return [Ref(target=href, children=_convert_children(tag))]
    return _convert_children(tag)


def _convert_blockquote(tag: Tag) -> list[Node]:
    """Convert a ``<blockquote>`` tag to a :class:`Blockquote` node.

    Only :class:`Paragraph` children are kept; other nodes are filtered out.

    Args:
        tag (Tag): The ``<blockquote>`` BeautifulSoup tag.

    Returns:
        List[Node]: A single-element list containing a :class:`Blockquote` node.
    """
    paras = [n for n in _convert_children(tag) if isinstance(n, Paragraph)]
    return [Blockquote(paragraphs=paras)]


def _convert_crossref(tag: Tag) -> list[Node]:
    """Convert an ``<awg-crossref>`` tag to a :class:`CrossRef` node.

    Returns an empty list if the ``n`` attribute is missing or non-numeric.

    Args:
        tag (Tag): The ``<awg-crossref>`` BeautifulSoup tag.

    Returns:
        List[Node]: A single :class:`CrossRef` node, or an empty list.
    """
    n_str = tag.get("n", "")
    if n_str.isdigit():
        return [CrossRef(n=int(n_str))]
    return []


def _convert_list(tag: Tag) -> list[Node]:
    """Convert a ``<ul>`` or ``<ol>`` tag to a :class:`ListBlock` node.

    Only :class:`ListItem` children are kept; other nodes are filtered out.

    Args:
        tag (Tag): The ``<ul>`` or ``<ol>`` BeautifulSoup tag.

    Returns:
        List[Node]: A single-element list containing a :class:`ListBlock` node.
    """
    items = [n for n in _convert_children(tag) if isinstance(n, ListItem)]
    return [ListBlock(items=items, ordered=tag.name == "ol")]


def _convert_note_p(p: Tag, note_id: str) -> Note:
    """Strip the backlink anchor and separator from a note ``<p>`` and convert it.

    Removes the ``<a class="note-backlink">`` anchor and the ``" | "`` separator
    that follows it, then returns a :class:`Note` built from the remaining children.

    Args:
        p (Tag): The ``<p>`` BeautifulSoup tag of the note.
        note_id (str): The ``id`` attribute value of *p*.

    Returns:
        Note: The converted note IR node.
    """
    backlink = p.find("a", class_="note-backlink")
    if backlink:
        backlink.decompose()
    first_text = next((c for c in p.children if isinstance(c, NavigableString)), None)
    if first_text and str(first_text).startswith(" | "):
        first_text.replace_with(str(first_text)[3:])
    return Note(id=note_id, children=_convert_children(p))


def _convert_sup(tag: Tag) -> list[Node]:
    """Convert a ``<sup>`` tag to a :class:`FootnoteRef` or :class:`Superscript` node.

    If the ``<sup>`` contains an ``<a id="note-ref-N">`` anchor it is treated as
    a footnote reference; otherwise it becomes a plain superscript.

    Args:
        tag (Tag): The ``<sup>`` BeautifulSoup tag.

    Returns:
        List[Node]: A single-element list containing either a
            :class:`FootnoteRef` or a :class:`Superscript` node.
    """
    for a_tag in tag.find_all("a", id=True):
        n = ReplacementUtils.parse_note_ref_id(a_tag.get("id", ""))
        if n is not None:
            return [FootnoteRef(n=n)]
    return [Superscript(children=_convert_children(tag))]


def _convert_table(bs_tag: Tag) -> Table:
    """Convert a ``<table>`` BeautifulSoup tag to a :class:`Table` IR node.

    Handles optional ``<thead>`` and ``<tbody>`` elements.  Rows inside
    ``<thead>`` are marked ``is_header=True``; rows inside ``<tbody>`` (or
    directly in the table when there is no ``<tbody>``) are data rows.

    Args:
        bs_tag (Tag): The ``<table>`` BeautifulSoup tag.

    Returns:
        Table: The parsed table IR node.
    """
    rows: list[Row] = []
    for tr in bs_tag.find_all("tr"):
        in_thead = tr.parent and tr.parent.name == "thead"
        cells: list[Cell] = []
        header_cells = tr.find_all("th", recursive=False)
        data_cells = tr.find_all("td", recursive=False)
        is_header = not in_thead and bool(header_cells) and not data_cells
        gap_before = "row-gap" in (tr.get("class") or [])
        text_center = "text-center" in (tr.get("class") or [])
        all_cells = (
            header_cells if is_header else tr.find_all(["th", "td"], recursive=False)
        )
        for cell_tag in all_cells:
            colspan_str = cell_tag.get("colspan")
            colspan = int(colspan_str) if colspan_str else None
            indent = "tab" in (cell_tag.get("class") or [])
            cells.append(
                Cell(
                    children=_convert_children(cell_tag), colspan=colspan, indent=indent
                )
            )
        rows.append(
            Row(
                cells=cells,
                is_header=is_header,
                gap_before=gap_before,
                text_center=text_center,
            )
        )
    return Table(rows=rows)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _prepare_html(html: str) -> str:
    """Prepare a raw HTML string for BeautifulSoup parsing.

    Applies :func:`~utils.replacement_utils.ReplacementUtils.replace_crossrefs`
    followed by :func:`~utils.replacement_utils.ReplacementUtils.strip_angular_bindings`.

    Args:
        html (str): The raw HTML string.

    Returns:
        str: The cleaned HTML string ready for parsing.
    """
    return ReplacementUtils.strip_angular_bindings(
        ReplacementUtils.replace_crossrefs(html)
    )
