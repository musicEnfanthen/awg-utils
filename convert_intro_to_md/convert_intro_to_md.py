#!/usr/bin/env python3
"""Convert AWG intro JSON (HTML block_content) to Markdown.

Produces one output file per locale found in the intro array,
named after the input file with the locale appended (e.g. intro_de.md, intro_en.md).

Usage:
    python convert_intro_to_md.py <path>/<to>/intro.json

Requires: markdownify (pip install -r requirements.txt --require-hashes)
"""

import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup, NavigableString, Tag

from utils.file_utils import FileUtils
from utils.processing_utils import ProcessingUtils


def convert_intro_to_md(intro: Dict, intro_locale: str) -> str:
    """Convert a single intro entry to Markdown and return the content.

    Args:
        intro (Dict): A single intro object from the JSON ``intro`` array.
        intro_locale (str): The locale string (e.g. ``'de'`` or ``'en'``) used to
            select the footnote section header.

    Returns:
        str: The fully converted Markdown string, with normalised whitespace and a
        trailing newline.
    """
    blocks = intro.get("content", [])

    md_lines: List[str] = []
    end_notes: Dict[str, str] = {}

    for block in blocks:
        header = (block.get("blockHeader") or "").strip()
        block_content = block.get("blockContent", [])
        block_notes = block.get("blockNotes", [])

        if header:
            md_lines.append(f"## {header}")
            md_lines.append("")

        md_lines.extend(ProcessingUtils.process_block_content(block_content))
        ProcessingUtils.process_block_notes(block_notes, end_notes)

    md_lines.extend(ProcessingUtils.process_end_notes(end_notes, intro_locale))

    return ProcessingUtils.assemble_markdown(md_lines)


def convert_intro_to_tei(intro: Dict, intro_locale: str) -> str:  # pylint: disable=too-many-locals
    """Convert a single intro entry to TEI XML and return the content as a string.

    Produces a stand-alone TEI document with:

    - A minimal ``<teiHeader>`` carrying the intro id and language.
    - A ``<text><body>`` where each block becomes a ``<div>``, with an optional
      ``<head>`` for block headers and block content converted to TEI elements.
    - A ``<back><div type="notes">`` section holding stand-off footnotes as
      ``<note>`` elements referenced from the body via ``<ptr target="#note-N"/>``..

    Args:
        intro (Dict): A single intro object from the JSON ``intro`` array.
        intro_locale (str): The locale string (e.g. ``'de'`` or ``'en'``) used
            to set ``xml:lang`` on the document root.

    Returns:
        str: A serialized TEI XML string with an XML declaration.
    """
    _tei_ns = "http://www.tei-c.org/ns/1.0"
    _xml_ns = "http://www.w3.org/XML/1998/namespace"
    _ang_re = re.compile(r"""\s*\([^)]+\)=(?:"[^"]*"|'[^']*')""")
    ET.register_namespace("", _tei_ns)
    ET.register_namespace("xml", _xml_ns)

    def _q(tag: str) -> str:
        return f"{{{_tei_ns}}}{tag}"

    def _xml(attr: str) -> str:
        return f"{{{_xml_ns}}}{attr}"

    def _strip_angular(html: str) -> str:
        return _ang_re.sub("", html)

    def _append_text(et_parent, text: str) -> None:
        children = list(et_parent)
        if children:
            last = children[-1]
            last.tail = (last.tail or "") + text
        else:
            et_parent.text = (et_parent.text or "") + text

    def _convert_node(bs_node, et_parent) -> None:  # pylint: disable=too-many-branches
        """Recursively convert a BeautifulSoup node to TEI ET elements."""
        if isinstance(bs_node, NavigableString):
            _append_text(et_parent, str(bs_node))
            return
        if not isinstance(bs_node, Tag):
            return

        tag = bs_node.name

        # Footnote reference: <sup><a id='note-ref-N'>N</a></sup>
        if tag == "sup":
            a_tag = bs_node.find("a", id=re.compile(r"^note-ref-\d+$"))
            if a_tag:
                m = re.match(r"note-ref-(\d+)", a_tag.get("id", ""))
                if m:
                    ptr = ET.SubElement(et_parent, _q("ptr"))
                    ptr.set("target", f"#note-{m.group(1)}")
                    return
            # Regular superscript
            hi = ET.SubElement(et_parent, _q("hi"))
            hi.set("rend", "super")
            for child in bs_node.children:
                _convert_node(child, hi)
            return

        if tag == "p":
            el = ET.SubElement(et_parent, _q("p"))
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag in ("em", "i"):
            el = ET.SubElement(et_parent, _q("hi"))
            el.set("rend", "italic")
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag in ("strong", "b"):
            el = ET.SubElement(et_parent, _q("hi"))
            el.set("rend", "bold")
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag == "a":
            href = bs_node.get("href")
            if href:
                el = ET.SubElement(et_parent, _q("ref"))
                el.set("target", href)
                for child in bs_node.children:
                    _convert_node(child, el)
            else:
                # Angular-only anchor — drop tag, keep content
                for child in bs_node.children:
                    _convert_node(child, et_parent)
        elif tag == "s":
            el = ET.SubElement(et_parent, _q("del"))
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag == "table":
            el = ET.SubElement(et_parent, _q("table"))
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag == "tbody":
            for child in bs_node.children:
                _convert_node(child, et_parent)
        elif tag == "tr":
            el = ET.SubElement(et_parent, _q("row"))
            for child in bs_node.children:
                _convert_node(child, el)
        elif tag == "td":
            el = ET.SubElement(et_parent, _q("cell"))
            cols = bs_node.get("colspan")
            if cols:
                el.set("cols", cols)
            for child in bs_node.children:
                _convert_node(child, el)
        else:
            # div, span, blockquote, unknown: transparent pass-through
            for child in bs_node.children:
                _convert_node(child, et_parent)

    def _parse_note(note_html: str):
        """Parse a blockNote HTML string to a ``(note_id, ET.Element)`` pair.

        Returns ``None`` if the note id cannot be found.
        """
        soup = BeautifulSoup(_strip_angular(note_html), "html.parser")
        p = soup.find("p")
        if not p:
            return None
        note_id = p.get("id")
        if not note_id:
            return None
        backlink = p.find("a", class_="note-backlink")
        if backlink:
            backlink.decompose()
        # Strip the " | " separator left after removing the backlink anchor
        first_text = next((c for c in p.children if isinstance(c, NavigableString)), None)
        if first_text and str(first_text).startswith(" | "):
            first_text.replace_with(str(first_text)[3:])
        note_el = ET.Element(_q("note"))
        note_el.set(_xml("id"), note_id)
        for child in list(p.children):
            _convert_node(child, note_el)
        return note_id, note_el

    def _convert_fragment(html: str, et_parent) -> None:
        soup = BeautifulSoup(_strip_angular(html), "html.parser")
        for child in list(soup.children):
            _convert_node(child, et_parent)

    # ------------------------------------------------------------------
    # Build the TEI tree
    # ------------------------------------------------------------------
    intro_id = intro.get("id", "")
    root = ET.Element(_q("TEI"))

    # teiHeader
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

    # text / body / back
    text_el = ET.SubElement(root, _q("text"))
    text_el.set(_xml("lang"), intro_locale)
    body = ET.SubElement(text_el, _q("body"))
    back = ET.SubElement(text_el, _q("back"))
    notes_div = ET.SubElement(back, _q("div"))
    notes_div.set("type", "notes")

    for block in intro.get("content", []):
        block_id = (block.get("blockId") or "").strip()
        header_text = (block.get("blockHeader") or "").strip()
        block_content = block.get("blockContent", [])
        block_notes = block.get("blockNotes", [])

        div = ET.SubElement(body, _q("div"))
        if block_id:
            div.set(_xml("id"), block_id)
        if header_text:
            ET.SubElement(div, _q("head")).text = header_text
        for html_fragment in block_content:
            _convert_fragment(html_fragment, div)
        for note_html in block_notes:
            parsed = _parse_note(note_html)
            if parsed:
                _, note_el = parsed
                notes_div.append(note_el)

    ET.indent(root, space="  ")
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue().decode("utf-8")


def get_intro_context(intro: Dict, output_path: Path) -> tuple[str, str, Path]:
    """Derive the id, locale, and locale-specific output path from an intro entry.

    Args:
        intro (Dict): A single intro object from the JSON ``intro`` array.
        output_path (Path): The base output path provided on the command line.

    Returns:
        tuple[str, str, Path]: A three-tuple of ``(intro_id, intro_locale, intro_output_path)``.
    """
    intro_id = intro.get("id", "")
    intro_locale = intro_id.split("-")[0] if intro_id and "-" in intro_id else intro_id
    intro_output_path = (
        output_path.with_name(f"{output_path.stem}_{intro_locale}{output_path.suffix}")
        if intro_locale
        else output_path
    )
    return intro_id, intro_locale, intro_output_path


def main():
    """Main function to read intro JSON, convert to Markdown, and write output files."""
    if len(sys.argv) < 2:
        print("Missing input JSON path.", file=sys.stderr)
        print(
            "Example: python convert_intro_to_md.py src/assets/.../intro.json",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".md")

    data = FileUtils.read_json(input_path)

    intros = data.get("intro", [])
    if not intros:
        print("No intro array found in input JSON.", file=sys.stderr)
        sys.exit(1)

    for intro in intros:
        intro_id, intro_locale, intro_output_path = get_intro_context(
            intro, output_path
        )

        intro_md = convert_intro_to_md(intro, intro_locale)

        FileUtils.write_md(intro_output_path, intro_md)

        print(f"Converted: {input_path} [{intro_id}]")
        print(f"Written:   {intro_output_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
