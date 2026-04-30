"""Utility functions for string replacement operations."""

import re


class ReplacementUtils:
    """A class that contains utility functions for string replacement operations."""

    _ANG_RE = re.compile(r"""\s*\(\w+\)=(?:"[^"]*"|'[^']*')""")
    _CROSSREF_RE = re.compile(
        r"<a\b(?![^>]*\bid=['\"]note-ref-)[^>]*fragmentId:\s*'note-(\d+)'[^>]*>\s*\d+\s*</a>",
        re.IGNORECASE,
    )
    _NOTE_REF_ID_RE = re.compile(r"^note-ref-(\d+)$")
    _ADJACENT_TABLES_RE = re.compile(r"(\|[^\n]*)\n\n(\|)")

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in the final Markdown string.

        Replaces non-breaking spaces (``\\xa0``) with regular spaces, collapses
        runs of three or more newlines to two, and strips leading/trailing whitespace.

        Args:
            text (str): The string to normalize.

        Returns:
            str: The normalized string.
        """
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def parse_note_ref_id(id_str: str) -> int | None:
        """Return the note number if *id_str* matches the pattern ``note-ref-N``.

        Args:
            id_str (str): The value of an HTML ``id`` attribute.

        Returns:
            int | None: The note number, or ``None`` if the string does not match.
        """
        m = ReplacementUtils._NOTE_REF_ID_RE.match(id_str)
        return int(m.group(1)) if m else None

    @staticmethod
    def replace_crossrefs(html: str) -> str:
        """Replace cross-reference anchors with a synthetic ``<awg-crossref n="N"/>`` tag.

        Must be applied BEFORE :meth:`strip_angular_bindings` so that ``fragmentId: 'note-N'`` is
        still present in the attribute string.

        Args:
            html (str): The raw HTML string possibly containing Angular cross-reference anchors.

        Returns:
            str: The HTML string with cross-reference anchors replaced by synthetic tags.
        """
        return ReplacementUtils._CROSSREF_RE.sub(
            lambda m: f'<awg-crossref n="{m.group(1)}"/>', html
        )

    @staticmethod
    def separate_adjacent_tables(text: str) -> str:
        """Insert a blank line between two consecutive Markdown tables.

        After whitespace normalization two back-to-back GFM tables are separated
        by only one blank line (``\\n\\n``).  This method restores the two blank
        lines (``\\n\\n\\n``) required to visually separate them by matching any
        line ending with ``|`` followed immediately by another line starting
        with ``|``.

        Args:
            text (str): The normalized Markdown string.

        Returns:
            str: The string with an extra blank line inserted between adjacent tables.
        """
        return ReplacementUtils._ADJACENT_TABLES_RE.sub(r"\1\n\n\n\2", text)

    @staticmethod
    def strip_angular_bindings(html: str) -> str:
        """Remove Angular event-binding attributes from an HTML string.

        Args:
            html (str): The HTML string to clean.

        Returns:
            str: The HTML string with all ``(eventName)="..."`` attributes removed.
        """
        return ReplacementUtils._ANG_RE.sub("", html)
