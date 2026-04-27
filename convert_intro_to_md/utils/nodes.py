"""Intermediate-representation (IR) node types for intro content.

These dataclasses form a format-neutral tree that the HTML parser produces and
that both the Markdown and TEI renderers consume.

Node hierarchy
--------------
Inline nodes (may appear inside block nodes):
    Text          — plain text run
    Italic        — *italic* / <em>
    Bold          — **bold** / <strong>
    Strikethrough — ~~strike~~ / <s>
    Superscript   — regular <sup>
    FootnoteRef   — footnote reference <sup><a id="note-ref-N">
    Ref           — hyperlink <a href="...">

Block nodes (top-level children of Block.content):
    Paragraph     — <p>
    Blockquote    — run of consecutive small paragraphs (<p class="small">)
    Table         — <table>

Helper nodes (nested inside Table/Row, not part of the Node union):
    Row           — <tr>  (is_header=True when all cells are <th>)
    Cell          — <td> / <th>

Structural nodes (not part of the Node union):
    Note          — one footnote / endnote
    Block         — one content block from the JSON (blockId + blockHeader + content + notes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# ---------------------------------------------------------------------------
# Inline nodes
# ---------------------------------------------------------------------------


@dataclass
class Text:
    """A plain text run."""

    value: str


@dataclass
class Italic:
    """Italic text — from <em> or <i>."""

    children: list[Node] = field(default_factory=list)


@dataclass
class Bold:
    """Bold text — from <strong> or <b>."""

    children: list[Node] = field(default_factory=list)


@dataclass
class Strikethrough:
    """Strikethrough text — from <s>."""

    children: list[Node] = field(default_factory=list)


@dataclass
class Superscript:
    """Regular superscript — from <sup> that is *not* a footnote reference."""

    children: list[Node] = field(default_factory=list)


@dataclass
class FootnoteRef:
    """An inline footnote reference — from <sup><a id="note-ref-N">N</a></sup>."""

    n: int


@dataclass
class CrossRef:
    """An inline cross-reference to a footnote — from <a (click)="...fragmentId: 'note-N'...">N</a>.

    Rendered as ``[N](#fnN)`` in Markdown and as ``<ref target="#note-N">N</ref>`` in TEI.
    """

    n: int


@dataclass
class Ref:
    """A hyperlink — from <a href="...">."""

    target: str
    children: list[Node] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Block nodes
# ---------------------------------------------------------------------------


@dataclass
class Paragraph:
    """A paragraph — from <p>."""

    children: list[Node] = field(default_factory=list)


@dataclass
class Blockquote:
    """A run of consecutive small paragraphs (<p class="small">) merged into one block."""

    paragraphs: list[Paragraph] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Table nodes
# ---------------------------------------------------------------------------


@dataclass
class Cell:
    """A table cell — from <td> or <th>."""

    children: list[Node] = field(default_factory=list)
    colspan: int | None = None


@dataclass
class Row:
    """A table row — from <tr>.  ``is_header=True`` when all cells are <th>."""

    cells: list[Cell] = field(default_factory=list)
    is_header: bool = False


@dataclass
class Table:
    """A table — from <table>."""

    rows: list[Row] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Node union
# ---------------------------------------------------------------------------

#: Union of all node types that may appear in a content tree.
Node = Union[
    Text,
    Italic,
    Bold,
    Strikethrough,
    Superscript,
    FootnoteRef,
    CrossRef,
    Ref,
    Paragraph,
    Blockquote,
    Table,
]


# ---------------------------------------------------------------------------
# Structural types
# ---------------------------------------------------------------------------


@dataclass
class Note:
    """A single footnote / endnote."""

    id: str
    children: list[Node] = field(default_factory=list)


@dataclass
class Block:
    """One content block from the JSON (corresponds to one blockId entry)."""

    id: str
    heading: list[Node] | None
    content: list[Node] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
