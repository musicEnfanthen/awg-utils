"""Parse AWG intro JSON blocks into format-neutral IR nodes (see utils/nodes.py)."""

import re
from typing import Dict, List

from bs4 import BeautifulSoup, NavigableString, Tag

from utils.nodes import (
    Block,
    Blockquote,
    Bold,
    Cell,
    CrossRef,
    FootnoteRef,
    Italic,
    Node,
    Note,
    Paragraph,
    Ref,
    Row,
    Strikethrough,
    Superscript,
    Table,
    Text,
)

# \w+ (not [^)]+) prevents the pattern from matching across "(<a (click)=" text content
_ANG_RE = re.compile(r"""\s*\(\w+\)=(?:"[^"]*"|'[^']*')""")
_CROSSREF_RE = re.compile(
    r"<a\b(?![^>]*\bid=['\"]note-ref-)[^>]*fragmentId:\s*'note-(\d+)'[^>]*>\s*\d+\s*</a>",
    re.IGNORECASE,
)
_NOTE_REF_ID_RE = re.compile(r"^note-ref-(\d+)$")
_SMALL_PARA_RE = re.compile(
    r"<p\b(?=[^>]*\bsmall\b)(?![^>]*\blist\b)[^>]*>", re.IGNORECASE
)


def parse_intro(intro: Dict) -> List[Block]:
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
# Block-content parsing
# ---------------------------------------------------------------------------

def _parse_block_content(block_content: List[str]) -> List[Node]:
    """Parse a list of HTML fragment strings into IR nodes.

    Consecutive small paragraphs (``<p class="small">``) are grouped into a
    single :class:`Blockquote` node.

    Args:
        block_content (List[str]): Raw HTML fragment strings from ``blockContent``.

    Returns:
        List[Node]: The parsed IR nodes in document order.
    """
    nodes: List[Node] = []
    i = 0
    while i < len(block_content):
        html = block_content[i]
        if _is_small_para(html):
            group = [html]
            while i + 1 < len(block_content) and _is_small_para(block_content[i + 1]):
                i += 1
                group.append(block_content[i])
            paras: List[Paragraph] = []
            for small_html in group:
                for node in _parse_fragment(small_html):
                    if isinstance(node, Paragraph):
                        paras.append(node)
            nodes.append(Blockquote(paragraphs=paras))
        else:
            nodes.extend(_parse_fragment(html))
        i += 1
    return nodes


def _parse_fragment(html: str) -> List[Node]:
    """Parse a single HTML fragment string into a list of IR nodes.

    Args:
        html (str): A raw HTML fragment string (may contain Angular bindings).

    Returns:
        List[Node]: The top-level IR nodes produced from the fragment.
    """
    soup = BeautifulSoup(_strip_angular(_preprocess_crossrefs(html)), "html.parser")
    nodes: List[Node] = []
    for child in soup.children:
        nodes.extend(_convert_node(child))
    return nodes


# ---------------------------------------------------------------------------
# Node conversion
# ---------------------------------------------------------------------------

def _convert_node(bs_node) -> List[Node]:  # pylint: disable=too-many-return-statements,too-many-branches
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

    if tag == "awg-crossref":
        n_str = bs_node.get("n", "")
        if n_str.isdigit():
            return [CrossRef(n=int(n_str))]
        return []

    # Footnote reference: <sup><a id="note-ref-N">N</a></sup>
    if tag == "sup":
        a_tag = bs_node.find("a", id=_NOTE_REF_ID_RE)
        if a_tag:
            m = _NOTE_REF_ID_RE.match(a_tag.get("id", ""))
            if m:
                return [FootnoteRef(n=int(m.group(1)))]
        return [Superscript(children=_convert_children(bs_node))]

    if tag == "p":
        return [Paragraph(children=_convert_children(bs_node))]
    if tag in ("em", "i"):
        return [Italic(children=_convert_children(bs_node))]
    if tag in ("strong", "b"):
        return [Bold(children=_convert_children(bs_node))]
    if tag == "a":
        href = bs_node.get("href")
        if href:
            return [Ref(target=href, children=_convert_children(bs_node))]
        # Angular-only anchor — transparent, keep content
        return _convert_children(bs_node)
    if tag == "s":
        return [Strikethrough(children=_convert_children(bs_node))]
    if tag == "table":
        return [_parse_table(bs_node)]
    # tbody is transparent; also div, span, blockquote, and unknown tags
    return _convert_children(bs_node)


def _convert_children(bs_node: Tag) -> List[Node]:
    """Convert all children of a BeautifulSoup tag to IR nodes.

    Args:
        bs_node (Tag): The parent BeautifulSoup tag.

    Returns:
        List[Node]: The concatenated IR nodes from all children.
    """
    nodes: List[Node] = []
    for child in bs_node.children:
        nodes.extend(_convert_node(child))
    return nodes


def _parse_table(bs_tag: Tag) -> Table:
    """Convert a ``<table>`` BeautifulSoup tag to a :class:`Table` IR node.

    Handles an optional intermediate ``<tbody>`` element.

    Args:
        bs_tag (Tag): The ``<table>`` BeautifulSoup tag.

    Returns:
        Table: The parsed table IR node.
    """
    container = bs_tag.find("tbody") or bs_tag
    rows: List[Row] = []
    for tr in container.find_all("tr", recursive=False):
        cells: List[Cell] = []
        header_cells = tr.find_all("th", recursive=False)
        data_cells = tr.find_all("td", recursive=False)
        is_header = bool(header_cells) and not data_cells
        for cell_tag in (header_cells if is_header else data_cells):
            colspan_str = cell_tag.get("colspan")
            colspan = int(colspan_str) if colspan_str else None
            cells.append(Cell(children=_convert_children(cell_tag), colspan=colspan))
        rows.append(Row(cells=cells, is_header=is_header))
    return Table(rows=rows)


# ---------------------------------------------------------------------------
# Note parsing
# ---------------------------------------------------------------------------

def _parse_block_notes(block_notes: List[str]) -> List[Note]:
    """Parse a list of blockNote HTML strings into :class:`Note` IR nodes.

    Args:
        block_notes (List[str]): Raw blockNote HTML strings from ``blockNotes``.

    Returns:
        List[Note]: The successfully parsed notes in source order.
    """
    notes: List[Note] = []
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
    soup = BeautifulSoup(_strip_angular(_preprocess_crossrefs(note_html)), "html.parser")
    p = soup.find("p")
    if not p:
        return None
    note_id = p.get("id")
    if not note_id:
        return None
    backlink = p.find("a", class_="note-backlink")
    if backlink:
        backlink.decompose()
    first_text = next((c for c in p.children if isinstance(c, NavigableString)), None)
    if first_text and str(first_text).startswith(" | "):
        first_text.replace_with(str(first_text)[3:])
    return Note(id=note_id, children=_convert_children(p))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _preprocess_crossrefs(html: str) -> str:
    """Replace cross-reference anchors with a synthetic ``<awg-crossref n="N"/>`` tag.

    Must be applied BEFORE :func:`_strip_angular` so that ``fragmentId: 'note-N'`` is
    still present in the attribute string.

    Args:
        html (str): The raw HTML string possibly containing Angular cross-reference anchors.

    Returns:
        str: The HTML string with cross-reference anchors replaced by synthetic tags.
    """
    return _CROSSREF_RE.sub(lambda m: f'<awg-crossref n="{m.group(1)}"/>', html)


def _strip_angular(html: str) -> str:
    """Remove Angular event-binding attributes from an HTML string.

    Args:
        html (str): The HTML string to clean.

    Returns:
        str: The HTML string with all ``(eventName)="..."`` attributes removed.
    """
    return _ANG_RE.sub("", html)


def _is_small_para(html: str) -> bool:
    """Return True if the HTML string is a small (non-list) paragraph.

    Args:
        html (str): An HTML fragment string.

    Returns:
        bool: True if the fragment opens with ``<p class="... small ...">``
        but does not also carry the ``list`` class.
    """
    return bool(_SMALL_PARA_RE.match(html.lstrip()))
