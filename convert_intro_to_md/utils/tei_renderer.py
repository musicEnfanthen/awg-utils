"""Render a list of Block IR nodes to a TEI XML string."""

import io
import xml.etree.ElementTree as ET
from typing import List

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

_TEI_NS = "http://www.tei-c.org/ns/1.0"
_XML_NS = "http://www.w3.org/XML/1998/namespace"


def render(blocks: List[Block], intro_id: str, intro_locale: str) -> str:
    """Render a list of Block IR nodes to a stand-alone TEI XML string.

    Produces a minimal TEI document with:

    - A ``<teiHeader>`` carrying the intro id and language.
    - A ``<text><body>`` where each block becomes a ``<div>``.
    - A ``<back><div type="notes">`` section with stand-off ``<note>`` elements.

    Args:
        blocks (List[Block]): The parsed IR blocks (from
            :func:`utils.html_parser.parse_intro`).
        intro_id (str): The intro identifier, used as the document title.
        intro_locale (str): The BCP-47 locale string (e.g. ``'de'`` or ``'en'``).

    Returns:
        str: A serialized TEI XML string with an XML declaration, UTF-8 encoded.
    """
    ET.register_namespace("", _TEI_NS)
    ET.register_namespace("xml", _XML_NS)

    root = ET.Element(_q("TEI"))

    _build_tei_header(root, intro_id, intro_locale)

    text_el = ET.SubElement(root, _q("text"))
    text_el.set(_xml("lang"), intro_locale)
    body = ET.SubElement(text_el, _q("body"))
    back = ET.SubElement(text_el, _q("back"))
    notes_div = ET.SubElement(back, _q("div"))
    notes_div.set("type", "notes")

    for block in blocks:
        div = ET.SubElement(body, _q("div"))
        if block.id:
            div.set(_xml("id"), block.id)
        if block.heading:
            head_el = ET.SubElement(div, _q("head"))
            for node in block.heading:
                _render_node(node, head_el)
        for node in block.content:
            _render_node(node, div)
        for note in block.notes:
            notes_div.append(_render_note(note))

    ET.indent(root, space="  ")
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue().decode("utf-8")


# ---------------------------------------------------------------------------
# teiHeader builder
# ---------------------------------------------------------------------------

def _build_tei_header(root: ET.Element, intro_id: str, intro_locale: str) -> None:
    """Append a minimal ``<teiHeader>`` to *root*.

    Args:
        root (ET.Element): The ``<TEI>`` root element.
        intro_id (str): Used as the document title.
        intro_locale (str): Used as the ``ident`` of the ``<language>`` element.
    """
    header = ET.SubElement(root, _q("teiHeader"))
    file_desc = ET.SubElement(header, _q("fileDesc"))
    title_stmt = ET.SubElement(file_desc, _q("titleStmt"))
    ET.SubElement(title_stmt, _q("title")).text = intro_id
    pub_stmt = ET.SubElement(file_desc, _q("publicationStmt"))
    ET.SubElement(pub_stmt, _q("p")).text = "AWG Online Edition"
    src_desc = ET.SubElement(file_desc, _q("sourceDesc"))
    ET.SubElement(src_desc, _q("p")).text = "Converted from AWG intro JSON"
    profile = ET.SubElement(header, _q("profileDesc"))
    lang_usage = ET.SubElement(profile, _q("langUsage"))
    ET.SubElement(lang_usage, _q("language")).set("ident", intro_locale)


# ---------------------------------------------------------------------------
# Node renderers
# ---------------------------------------------------------------------------

def _render_node(node: Node, parent: ET.Element) -> None:  # pylint: disable=too-many-branches
    """Render a single IR node as a child of *parent*.

    Args:
        node (Node): The IR node to render.
        parent (ET.Element): The ET element to attach rendered output to.
    """
    if isinstance(node, Text):
        _append_text(parent, node.value)
    elif isinstance(node, FootnoteRef):
        ptr = ET.SubElement(parent, _q("ptr"))
        ptr.set("target", f"#note-{node.n}")
    elif isinstance(node, CrossRef):
        el = ET.SubElement(parent, _q("ref"))
        el.set("target", f"#note-{node.n}")
        el.text = str(node.n)
    elif isinstance(node, Ref):
        el = ET.SubElement(parent, _q("ref"))
        el.set("target", node.target)
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Italic):
        el = ET.SubElement(parent, _q("hi"))
        el.set("rend", "italic")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Bold):
        el = ET.SubElement(parent, _q("hi"))
        el.set("rend", "bold")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Strikethrough):
        el = ET.SubElement(parent, _q("del"))
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Superscript):
        el = ET.SubElement(parent, _q("hi"))
        el.set("rend", "super")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Paragraph):
        el = ET.SubElement(parent, _q("p"))
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Blockquote):
        for para in node.paragraphs:
            el = ET.SubElement(parent, _q("p"))
            for child in para.children:
                _render_node(child, el)
    elif isinstance(node, Table):
        _render_table(node, parent)


def _render_table(node: Table, parent: ET.Element) -> None:
    """Render a :class:`~utils.nodes.Table` IR node as a TEI ``<table>``.

    Args:
        node (Table): The table IR node.
        parent (ET.Element): The ET element to attach the ``<table>`` to.
    """
    table_el = ET.SubElement(parent, _q("table"))
    for row in node.rows:
        _render_row(row, table_el)


def _render_row(node: Row, parent: ET.Element) -> None:
    """Render a :class:`~utils.nodes.Row` IR node as a TEI ``<row>``.

    Args:
        node (Row): The row IR node.
        parent (ET.Element): The ET element to attach the ``<row>`` to.
    """
    row_el = ET.SubElement(parent, _q("row"))
    if node.is_header:
        row_el.set("role", "label")
    for cell in node.cells:
        _render_cell(cell, row_el)


def _render_cell(node: Cell, parent: ET.Element) -> None:
    """Render a :class:`~utils.nodes.Cell` IR node as a TEI ``<cell>``.

    Args:
        node (Cell): The cell IR node.
        parent (ET.Element): The ET element to attach the ``<cell>`` to.
    """
    cell_el = ET.SubElement(parent, _q("cell"))
    if node.colspan is not None:
        cell_el.set("cols", str(node.colspan))
    for child in node.children:
        _render_node(child, cell_el)


def _render_note(note: Note) -> ET.Element:
    """Render a :class:`~utils.nodes.Note` IR node as a TEI ``<note>`` element.

    Args:
        note (Note): The note IR node.

    Returns:
        ET.Element: A ``<note xml:id="...">`` element with rendered children.
    """
    note_el = ET.Element(_q("note"))
    note_el.set(_xml("id"), note.id)
    for child in note.children:
        _render_node(child, note_el)
    return note_el


# ---------------------------------------------------------------------------
# ET helpers
# ---------------------------------------------------------------------------

def _q(tag: str) -> str:
    """Return a Clark-notation qualified name in the TEI namespace.

    Args:
        tag (str): The local tag name.

    Returns:
        str: ``{http://www.tei-c.org/ns/1.0}tag``.
    """
    return f"{{{_TEI_NS}}}{tag}"


def _xml(attr: str) -> str:
    """Return a Clark-notation qualified name in the XML namespace.

    Args:
        attr (str): The local attribute name.

    Returns:
        str: ``{http://www.w3.org/XML/1998/namespace}attr``.
    """
    return f"{{{_XML_NS}}}{attr}"


def _append_text(parent: ET.Element, text: str) -> None:
    """Append *text* to *parent*, correctly handling mixed content.

    If *parent* already has child elements the text is appended to the
    ``tail`` of the last child; otherwise it is appended to ``parent.text``.

    Args:
        parent (ET.Element): The element to append text to.
        text (str): The text string to append.
    """
    children = list(parent)
    if children:
        last = children[-1]
        last.tail = (last.tail or "") + text
    else:
        parent.text = (parent.text or "") + text
