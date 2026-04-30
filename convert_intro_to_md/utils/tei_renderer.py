"""Render a list of Block IR nodes to a TEI XML string."""

import io
import xml.etree.ElementTree as ET

from utils.nodes import (
    Block,
    Blockquote,
    Bold,
    Cell,
    CrossRef,
    FootnoteRef,
    Italic,
    ListBlock,
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

_TEI_NS = "http://www.tei-c.org/ns/1.0"
_XML_NS = "http://www.w3.org/XML/1998/namespace"

# Module-level notes lookup; populated by render() before walking the tree.
_notes_lookup: dict[int, Note] = {}


def render(blocks: list[Block], intro_id: str, intro_locale: str) -> str:
    """Render a list of Block IR nodes to a stand-alone TEI XML string.

    Produces a minimal TEI document with:

    - A ``<teiHeader>`` carrying the intro id and language.
    - A ``<text><body>`` where each block becomes a ``<div>``.
    - Footnotes rendered inline as ``<note place="end" n="N">`` elements.

    Args:
        blocks (List[Block]): The parsed IR blocks (from
            :func:`utils.html_parser.parse_intro`).
        intro_id (str): The intro identifier, used as the document title.
        intro_locale (str): The BCP-47 locale string (e.g. ``'de'`` or ``'en'``).

    Returns:
        str: A serialized TEI XML string with an XML declaration, UTF-8 encoded.
    """
    global _notes_lookup  # pylint: disable=global-statement
    ET.register_namespace("", _TEI_NS)
    ET.register_namespace("xml", _XML_NS)

    _notes_lookup = {}
    for block in blocks:
        for note in block.notes:
            try:
                _notes_lookup[int(note.id.split("-")[-1])] = note
            except (ValueError, IndexError):
                pass

    root = ET.Element(_tei("TEI"))

    _build_tei_header(root, intro_id, intro_locale)

    text_el = ET.SubElement(root, _tei("text"))
    text_el.set(_xml("lang"), intro_locale)
    body = ET.SubElement(text_el, _tei("body"))

    for block in blocks:
        div = ET.SubElement(body, _tei("div"))
        if block.id:
            div.set(_xml("id"), block.id)
        if block.heading:
            head_el = ET.SubElement(div, _tei("head"))
            for node in block.heading:
                _render_node(node, head_el)
        for node in block.content:
            _render_node(node, div)

    _notes_lookup = {}

    ET.indent(root, space="  ")
    _fix_mixed_content_indent(root)
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
    header = ET.SubElement(root, _tei("teiHeader"))
    file_desc = ET.SubElement(header, _tei("fileDesc"))
    title_stmt = ET.SubElement(file_desc, _tei("titleStmt"))
    ET.SubElement(title_stmt, _tei("title")).text = intro_id
    pub_stmt = ET.SubElement(file_desc, _tei("publicationStmt"))
    ET.SubElement(pub_stmt, _tei("p")).text = "AWG Online Edition"
    src_desc = ET.SubElement(file_desc, _tei("sourceDesc"))
    ET.SubElement(src_desc, _tei("p")).text = "Converted from AWG intro JSON"
    profile = ET.SubElement(header, _tei("profileDesc"))
    lang_usage = ET.SubElement(profile, _tei("langUsage"))
    ET.SubElement(lang_usage, _tei("language")).set("ident", intro_locale)


# ---------------------------------------------------------------------------
# Node renderers
# ---------------------------------------------------------------------------


def _render_node(node: Node, parent: ET.Element) -> None:  # pylint: disable=too-many-branches,too-many-statements
    """Render a single IR node as a child of *parent*.

    Args:
        node (Node): The IR node to render.
        parent (ET.Element): The ET element to attach rendered output to.
    """
    if isinstance(node, Text):
        _append_text(parent, node.value)
    elif isinstance(node, FootnoteRef):
        note_el = ET.SubElement(parent, _tei("note"))
        note_el.set("place", "end")
        note_el.set("n", str(node.n))
        note = _notes_lookup.get(node.n)
        if note:
            for child in note.children:
                _render_node(child, note_el)
    elif isinstance(node, CrossRef):
        el = ET.SubElement(parent, _tei("ref"))
        el.set("target", f"#note-{node.n}")
        el.text = str(node.n)
    elif isinstance(node, Ref):
        el = ET.SubElement(parent, _tei("ref"))
        el.set("target", node.target)
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Italic):
        el = ET.SubElement(parent, _tei("hi"))
        el.set("rend", "italic")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Bold):
        el = ET.SubElement(parent, _tei("hi"))
        el.set("rend", "bold")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Strikethrough):
        el = ET.SubElement(parent, _tei("del"))
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Underline):
        el = ET.SubElement(parent, _tei("hi"))
        el.set("rend", "underline")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Superscript):
        el = ET.SubElement(parent, _tei("hi"))
        el.set("rend", "sup")
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Paragraph):
        el = ET.SubElement(parent, _tei("p"))
        for child in node.children:
            _render_node(child, el)
    elif isinstance(node, Blockquote):
        quote_el = ET.SubElement(parent, _tei("quote"))
        for para in node.paragraphs:
            el = ET.SubElement(quote_el, _tei("l"))
            for child in para.children:
                _render_node(child, el)
    elif isinstance(node, ListBlock):
        list_el = ET.SubElement(parent, _tei("list"))
        if node.ordered:
            list_el.set("rend", "ordered")
        for item in node.items:
            item_el = ET.SubElement(list_el, _tei("item"))
            for child in item.children:
                _render_node(child, item_el)
    elif isinstance(node, Table):
        _render_table(node, parent)


def _render_table(node: Table, parent: ET.Element) -> None:
    """Render a :class:`~utils.nodes.Table` IR node as a TEI ``<table>``.

    Args:
        node (Table): The table IR node.
        parent (ET.Element): The ET element to attach the ``<table>`` to.
    """
    table_el = ET.SubElement(parent, _tei("table"))
    for row in node.rows:
        _render_row(row, table_el)


def _render_row(node: Row, parent: ET.Element) -> None:
    """Render a :class:`~utils.nodes.Row` IR node as a TEI ``<row>``.

    Args:
        node (Row): The row IR node.
        parent (ET.Element): The ET element to attach the ``<row>`` to.
    """
    row_el = ET.SubElement(parent, _tei("row"))
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
    cell_el = ET.SubElement(parent, _tei("cell"))
    if node.colspan is not None:
        cell_el.set("cols", str(node.colspan))
    for child in node.children:
        _render_node(child, cell_el)


# ---------------------------------------------------------------------------
# ET helpers
# ---------------------------------------------------------------------------


def _fix_mixed_content_indent(elem: ET.Element) -> None:
    """Remove spurious whitespace-only text added by ET.indent() to inline elements.

    ET.indent() unconditionally adds newline + spaces as the ``.tail`` of
    every element, including inline ones (e.g. ``<hi>``, ``<ref>``, ``<ptr>``),
    and as the ``.text`` of elements whose first child is an element rather than
    text.  Inside mixed-content parents those injected newlines become visible
    text.  This function walks the tree and resets whitespace-only ``.tail``
    values from children, and the whitespace-only ``.text`` of the element
    itself, for any element that contains mixed content.

    Args:
        elem (ET.Element): The root of the element tree to fix.
    """
    children = list(elem)
    has_real_text = bool(elem.text and elem.text.strip())
    has_tailed_child = any(c.tail and c.tail.strip() for c in children)
    if has_real_text or has_tailed_child:
        if elem.text and not elem.text.strip():
            elem.text = None
        for child in children:
            if child.tail and not child.tail.strip():
                child.tail = None
    for child in children:
        _fix_mixed_content_indent(child)


def _tei(tag: str) -> str:
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
