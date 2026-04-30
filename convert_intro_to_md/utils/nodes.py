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
    Underline     — <u>underline</u> / <hi rend="underline">
    Superscript   — regular <sup>
    FootnoteRef   — footnote reference <sup><a id="note-ref-N">
    Ref           — hyperlink <a href="...">

Block nodes (top-level children of Block.content):
    Paragraph     — <p>
    Blockquote    — <blockquote>
    List          — <ul> / <ol>
    Table         — <table>

Helper nodes (nested inside List, not part of the Node union):
    ListItem      — <li>

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
class Underline:
    """Underlined text — from <u>."""

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
    """A blockquote block — from <blockquote>."""

    paragraphs: list[Paragraph] = field(default_factory=list)


# ---------------------------------------------------------------------------
# List nodes
# ---------------------------------------------------------------------------


@dataclass
class ListItem:
    """A list item — from <li>."""

    children: list[Node] = field(default_factory=list)


@dataclass
class ListBlock:
    """A list block — from <ul> (ordered=False) or <ol> (ordered=True)."""

    items: list[ListItem] = field(default_factory=list)
    ordered: bool = False


# ---------------------------------------------------------------------------
# Table nodes
# ---------------------------------------------------------------------------


@dataclass
class Cell:
    """A table cell — from <td> or <th>.  ``indent=True`` when the cell carries
    ``class="tab"`` (visually indented row in a hierarchical table)."""

    children: list[Node] = field(default_factory=list)
    colspan: int | None = None
    indent: bool = False


@dataclass
class Row:
    """A table row — from <tr>.  ``is_header=True`` when all cells are <th>.
    ``gap_before=True`` when the row carries ``class="row-gap"``.
    ``text_center=True`` when the row carries ``class="text-center"``."""

    cells: list[Cell] = field(default_factory=list)
    is_header: bool = False
    gap_before: bool = False
    text_center: bool = False


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
    Underline,
    Superscript,
    FootnoteRef,
    CrossRef,
    Ref,
    Paragraph,
    Blockquote,
    ListBlock,
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
