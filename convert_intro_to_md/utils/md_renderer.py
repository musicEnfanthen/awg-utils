"""Render a list of Block IR nodes to a Markdown string."""

import sys

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
from utils.replacement_utils import ReplacementUtils

_INLINE_WRAP: dict[type, tuple[str, str]] = {
    Italic: ("*", "*"),
    Bold: ("**", "**"),
    Strikethrough: ("~~", "~~"),
    Underline: ("<u>", "</u>"),
    Superscript: ("<sup>", "</sup>"),
    Paragraph: ("", ""),
}


def render(blocks: list[Block], intro_locale: str) -> str:
    """Render a list of Block IR nodes to a Markdown string.

    Args:
        blocks (List[Block]): The parsed IR blocks to render.
        intro_locale (str): The locale string (e.g. ``'en'`` or ``'de'``) used to
            select the footnotes section header.

    Returns:
        str: The fully normalized Markdown string with a trailing newline.
    """
    lines: list[str] = []
    all_notes: dict[int, Note] = {}
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
    text = ReplacementUtils.normalize_whitespace("\n".join(lines))
    text = ReplacementUtils.separate_adjacent_tables(text)
    return text + "\n"


def _collect_note(note: Note, notes: dict[int, Note]) -> None:
    """Insert a note into the accumulator dict, warning on duplicates.

    Args:
        note (Note): The note node to collect.
        notes (dict[int, Note]): The accumulator mapping note number to Note.
    """
    n = int(note.id.split("-")[-1])
    if n in notes:
        print(
            f"Duplicate note number {n!r} encountered; keeping first.",
            file=sys.stderr,
        )
    else:
        notes[n] = note


def _render_notes(notes: dict[int, Note], locale: str) -> list[str]:
    """Build the footnotes section lines from the collected notes.

    Args:
        notes (dict[int, Note]): A mapping of note number to Note node.
        locale (str): The locale string used to select the section header.

    Returns:
        List[str]: The Markdown lines for the footnotes section,
        or an empty list if *notes* is empty.
    """
    if not notes:
        return []
    header = "Notes" if locale == "en" else "Anmerkungen"
    lines: list[str] = ["---", "", f"## {header}", ""]
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
        return _render_blockquote(node)
    if isinstance(node, ListBlock):
        return _render_list(node)
    if isinstance(node, Table):
        return _render_table(node)
    return _render_inline(node)


def _render_inline(node: Node) -> str:  # pylint: disable=too-many-return-statements
    """Render a single IR node to an inline Markdown string.

    Args:
        node (Node): The node to render.

    Returns:
        str: The rendered inline Markdown string.
    """
    wrap = _INLINE_WRAP.get(type(node))
    if wrap is not None:
        pre, suf = wrap
        return f"{pre}{_render_inline_children(node.children)}{suf}"
    if isinstance(node, Text):
        return node.value.replace("\xa0", " ")
    if isinstance(node, FootnoteRef):
        return f"[^{node.n}]"
    if isinstance(node, CrossRef):
        return f"[{node.n}](#fn:{node.n})"
    if isinstance(node, Ref):
        return f"[{_render_inline_children(node.children)}]({node.target})"

    if isinstance(node, Blockquote):
        return " ".join(_render_inline_children(p.children) for p in node.paragraphs)
    if isinstance(node, ListBlock):
        return " ".join(_render_inline_children(item.children) for item in node.items)
    return ""  # Table inline → empty


def _render_inline_children(children: list[Node]) -> str:
    """Render a sequence of inline IR nodes to a concatenated Markdown string.

    Args:
        children (List[Node]): The child nodes to render.

    Returns:
        str: The concatenated Markdown string.
    """
    return "".join(_render_inline(n) for n in children)


def _render_blockquote(node: Blockquote) -> str:
    """Render a Blockquote IR node to a Markdown string.

    Args:
        node (Blockquote): The blockquote node to render.

    Returns:
        str: The rendered Markdown string.
    """
    parts = ["> " + _render_inline_children(p.children) for p in node.paragraphs]
    return "\n>\n".join(parts)


def _render_list(node: ListBlock) -> str:
    """Render a ListBlock IR node to a Markdown string.

    Args:
        node (ListBlock): The list node to render.

    Returns:
        str: The rendered Markdown string.
    """
    if node.ordered:
        lines = [
            f"{i + 1}. {_render_inline_children(item.children)}"
            for i, item in enumerate(node.items)
        ]
    else:
        lines = ["- " + _render_inline_children(item.children) for item in node.items]
    return "\n".join(lines)


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
    empty_row = "|" + "|".join(" " for _ in range(num_cols)) + "|"
    output_rows: list[str] = []
    for row, rendered in zip(rows, rendered_rows):
        if row.gap_before:
            output_rows.append(empty_row)
        output_rows.append(rendered)
    separator = "|" + "|".join(f" {'---'} " for _ in range(num_cols)) + "|"
    if rows[0].is_header:
        return "\n".join([output_rows[0], separator] + output_rows[1:])
    blank_header = "|" + "|".join("  " for _ in range(num_cols)) + "|"
    return "\n".join([blank_header, separator] + output_rows)


def _render_table_row(row: Row, num_cols: int) -> str:
    """Render a Row IR node to a single GFM table row string.

    Args:
        row (Row): The row node to render.
        num_cols (int): The total number of columns in the table.

    Returns:
        str: The rendered Markdown table row string.
    """
    cells: list[str] = []
    # Single full-width cell: center only when text-center AND odd col count, else first col
    if len(row.cells) == 1 and (row.cells[0].colspan or 1) == num_cols:
        content = _render_cell_content(row.cells[0])
        mid = num_cols // 2 if (row.text_center and num_cols % 2 != 0) else 0
        cells = [""] * mid + [content] + [""] * (num_cols - mid - 1)
        return "|" + "|".join(f" {c} " if c else " " for c in cells) + "|"
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
    prefix = "&ensp;&ensp;" if cell.indent else ""
    return prefix + _render_inline_children(cell.children).replace("|", r"\|")
