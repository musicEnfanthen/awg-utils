#!/usr/bin/env python3
"""Convert AWG intro JSON (HTML block_content) to Markdown.

Produces one output file per locale found in the intro array,
named after the input file with the locale appended (e.g. intro_de.md, intro_en.md).

Usage:
    python convert_intro_to_md.py <path>/<to>/intro.json

Requires: markdownify (pip install -r requirements.txt --require-hashes)
"""

import sys
from pathlib import Path
from typing import Dict

from utils.file_utils import FileUtils
from utils.html_parser import parse_intro
from utils.nodes import Block
from utils import md_renderer, tei_renderer


def convert_intro_to_md(blocks: list[Block], intro_locale: str) -> str:
    """Convert parsed intro blocks to Markdown and return the content.

    Args:
        blocks (list[Block]): Parsed IR blocks from :func:`~utils.html_parser.parse_intro`.
        intro_locale (str): The locale string (e.g. ``'de'`` or ``'en'``) used to
            select the footnote section header.

    Returns:
        str: The fully converted Markdown string, with normalised whitespace and a
        trailing newline.
    """
    return md_renderer.render(blocks, intro_locale)


def convert_intro_to_tei(blocks: list[Block], intro_id: str, intro_locale: str) -> str:
    """Convert parsed intro blocks to TEI XML and return the content as a string.

    Produces a stand-alone TEI document with:

    - A minimal ``<teiHeader>`` carrying the intro id and language.
    - A ``<text><body>`` where each block becomes a ``<div>``, with an optional
      ``<head>`` for block headers and block content converted to TEI elements.
    - Footnotes rendered inline as ``<note place="end" n="N">`` elements.

    Args:
        blocks (list[Block]): Parsed IR blocks from :func:`~utils.html_parser.parse_intro`.
        intro_id (str): The id string from the intro object (e.g. ``'de-1'``).
        intro_locale (str): The locale string (e.g. ``'de'`` or ``'en'``) used
            to set ``xml:lang`` on the document root.

    Returns:
        str: A serialized TEI XML string with an XML declaration.
    """
    return tei_renderer.render(blocks, intro_id, intro_locale)


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
        blocks = parse_intro(intro)

        intro_md = convert_intro_to_md(blocks, intro_locale)
        intro_tei = convert_intro_to_tei(blocks, intro_id, intro_locale)

        FileUtils.write_file(intro_output_path.with_suffix(".md"), intro_md)
        FileUtils.write_file(intro_output_path.with_suffix(".tei"), intro_tei)

        print(f"Converted: {input_path} [{intro_id}]")
        print(f"Written:   {intro_output_path.with_suffix('.md')}")
        print(f"Written:   {intro_output_path.with_suffix('.tei')}")


if __name__ == "__main__":  # pragma: no cover
    main()
