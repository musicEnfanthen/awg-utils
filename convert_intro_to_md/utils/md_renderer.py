"""Render a list of Block IR nodes to a Markdown string."""

import sys
from typing import Dict, List

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
from utils.replacement_utils import ReplacementUtils


def render(blocks: List[Block], intro_locale: str) -> str:
    """Render a list of Block IR nodes to a Markdown string.

    Args:
        blocks (List[Block]): The parsed IR blocks to render.
        intro_locale (str): The locale string (e.g. ``'en'`` or ``'de'``) used to
            select the footnotes section header.

    Returns:
        str: The fully normalized Markdown string with a trailing newline.
    """
    lines: List[str] = []
    all_notes: Dict[int, Note] = {}
    for block in blocks:
        if block.heading:
            lines.append("## " + _render_inline_children(block.heading))
            lines.append("")
        for node in block.content:
            rendered = _render_block(node)
            if rendered:
                lines.append(rendered)
                lines.append("")
        for note in block.notes:
            _collect_note(note, all_notes)
    lines.extend(_render_notes(all_notes, intro_locale))
    return ReplacementUtils.normalize_whitespace("\n".join(lines)) + "\n"


def _collect_note(note: Note, notes: Dict[int, Note]) -> None:
    """Insert a note into the accumulator dict, warning on duplicates.

    Args:
        note (Note): The note node to collect.
        notes (Dict[int, Note]): The accumulator mapping note number to Note.
    """
    n = int(note.id.split("-")[-1])
    if n in notes:
        print(
            f"Duplicate note number {n!r} encountered; keeping first.",
            file=sys.stderr,
        )
    else:
        notes[n] = note


def _render_notes(notes: Dict[int, Note], locale: str) -> List[str]:
    """Build the footnotes section lines from the collected notes.

    Args:
        notes (Dict[int, Note]): A mapping of note number to Note node.
        locale (str): The locale string used to select the section header.

    Returns:
        List[str]: The Markdown lines for the footnotes section,
        or an empty list if *notes* is empty.
    """
    if not notes:
        return []
    header = "Notes" if locale == "en" else "Anmerkungen"
    lines: List[str] = ["---", "", f"## {header}", ""]
    for n in sorted(notes):
        content = _render_inline_children(notes[n].children)
        lines.append(f"[^{n}]: | {content}")
        lines.append("")
    return lines


def _render_block(node: Node) -> str:
    """Render a block-level IR node to a Markdown string.

    Args:
        node (Node): The block node to render.

    Returns:
        str: The rendered Markdown string (may be empty for unsupported node types).
    """
    if isinstance(node, Paragraph):
        return _render_inline_children(node.children)
    if isinstance(node, Blockquote):
        parts = ["> " + _render_inline_children(p.children) for p in node.paragraphs]
        return "\n>\n".join(parts)
    if isinstance(node, Table):
        return _render_table(node)
    return _render_inline(node)


def _render_inline_children(children: List[Node]) -> str:
    """Render a sequence of inline IR nodes to a concatenated Markdown string.

    Args:
        children (List[Node]): The child nodes to render.

    Returns:
        str: The concatenated Markdown string.
    """
    return "".join(_render_inline(n) for n in children)


def _render_inline(node: Node) -> str:  # pylint: disable=too-many-return-statements
    """Render a single IR node to an inline Markdown string.

    Args:
        node (Node): The node to render.

    Returns:
        str: The rendered inline Markdown string.
    """
    if isinstance(node, Text):
        return node.value.replace("\xa0", " ")
    if isinstance(node, FootnoteRef):
        return f"[^{node.n}]"
    if isinstance(node, CrossRef):
        return f"[{node.n}](#fn{node.n})"
    if isinstance(node, Ref):
        return f"[{_render_inline_children(node.children)}]({node.target})"
    if isinstance(node, Italic):
        return f"*{_render_inline_children(node.children)}*"
    if isinstance(node, Bold):
        return f"**{_render_inline_children(node.children)}**"
    if isinstance(node, Strikethrough):
        return f"~~{_render_inline_children(node.children)}~~"
    if isinstance(node, Superscript):
        return f"<sup>{_render_inline_children(node.children)}</sup>"
    if isinstance(node, Paragraph):
        return _render_inline_children(node.children)
    if isinstance(node, Blockquote):
        return " ".join(_render_inline_children(p.children) for p in node.paragraphs)
    return ""  # Table inline → empty


def _render_table(node: Table) -> str:
    """Render a Table IR node to a GFM Markdown table string.

    Args:
        node (Table): The table node to render.

    Returns:
        str: The rendered Markdown table string, or an empty string for empty tables.
    """
    rows = [r for r in node.rows if r.cells]
    if not rows:
        return ""
    num_cols = max(sum(c.colspan or 1 for c in r.cells) for r in rows)
    if num_cols == 0:
        return ""
    rendered_rows = [_render_table_row(r, num_cols) for r in rows]
    separator = "|" + "|".join(f" {'---'} " for _ in range(num_cols)) + "|"
    if rows[0].is_header:
        return "\n".join([rendered_rows[0], separator] + rendered_rows[1:])
    blank_header = "|" + "|".join("  " for _ in range(num_cols)) + "|"
    return "\n".join([blank_header, separator] + rendered_rows)


def _render_table_row(row: Row, num_cols: int) -> str:
    """Render a Row IR node to a single GFM table row string.

    Args:
        row (Row): The row node to render.
        num_cols (int): The total number of columns in the table.

    Returns:
        str: The rendered Markdown table row string.
    """
    cells: List[str] = []
    for cell in row.cells:
        cells.append(_render_cell_content(cell))
        for _ in range((cell.colspan or 1) - 1):
            cells.append("")
    while len(cells) < num_cols:
        cells.append("")
    return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"


def _render_cell_content(cell: Cell) -> str:
    """Render the inline content of a Cell IR node, escaping pipe characters.

    Args:
        cell (Cell): The cell node to render.

    Returns:
        str: The rendered cell content with ``|`` escaped as ``\\|``.
    """
    return _render_inline_children(cell.children).replace("|", r"\|")
