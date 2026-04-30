# Testing Guide for convert_intro_to_md

This directory contains tests for `convert_intro_to_md.py` and its utility modules under `utils/`.

## Project Structure

```
convert_intro_to_md/
├── convert_intro_to_md.py    # Main script: orchestrates JSON → Markdown/TEI conversion
├── utils/
│   ├── __init__.py
│   ├── file_utils.py         # File I/O: reading JSON, writing output files
│   ├── html_parser.py        # HTML parser: converts JSON block content to IR nodes
│   ├── md_renderer.py        # Markdown renderer: renders IR nodes to GFM Markdown
│   ├── nodes.py              # IR node dataclasses (Text, Bold, Italic, Table, etc.)
│   ├── replacement_utils.py  # Markdown post-processing: whitespace and table separation
│   └── tei_renderer.py       # TEI renderer: renders IR nodes to TEI XML
├── tests/
│   ├── data/
│   │   ├── intro.json
│   │   ├── intro_de.md
│   │   ├── intro_de.tei
│   │   └── intro_en.md
│   ├── __init__.py
│   ├── test_convert_intro_to_md.py
│   ├── test_file_utils.py
│   └── test_replacement_utils.py
├── requirements.txt
└── pytest.ini
```

## Setup

See the [Virtual Environments](../../README.md#virtual-environments) section in the repo-level README for how to create and activate a virtual environment.

Once the virtual environment is active, install dependencies:

```bash
pip install -r requirements.txt --require-hashes
```

## Running Tests

```bash
# Run all tests
pytest .

# Run with verbose output
pytest . -v

# Run a specific test module
pytest tests/test_replacement_utils.py -v
```

## Coverage

```bash
# Run with coverage (configured in pytest.ini)
pytest . --cov=utils --cov=convert_intro_to_md --cov-report=html --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

Test modules are listed alphabetically.

---

### Main Script Tests (`test_convert_intro_to_md.py`)

Tests for the public functions in `convert_intro_to_md.py`.

#### `TestConvertIntroToMd`

Tests for `convert_intro_to_md(intro, intro_locale)`:

- Returns a string for any valid intro dict.
- An intro with no content blocks produces a bare newline.
- Block headers are rendered as `## <header>` lines.
- Null or whitespace-only block headers are skipped.
- Delegates to `md_renderer.render`.
- A missing `content` key is handled gracefully.

#### `TestGetIntroContext`

Tests for `get_intro_context(intro, output_path)`:

- The locale is extracted as the segment before the first hyphen in the id.
- The full intro id is returned unchanged.
- The output path has the locale appended before the file extension.
- An id with no hyphen is used directly as the locale.
- A missing id leaves the output path unchanged.
- The output file is placed in the same directory as the base path.

#### `TestMain`

Tests for `main()`:

- Exits with code 1 when no arguments are provided.
- Prints a usage example to stderr when no args are given.
- Exits when the JSON has no `intro` key.
- Prints an error message to stderr when the intro array is missing.
- Writes an output file for each intro entry.
- Writes one file per locale for multi-locale input.
- Prints `Converted:` and `Written:` lines for each processed intro.

---

### File Utils Tests (`test_file_utils.py`)

Tests for `FileUtils` in `utils/file_utils.py`.

#### `TestReadJson`

Tests for `read_json(file_path)`:

- A valid JSON file is read and returned as a dict.
- Nested JSON structures are parsed correctly.
- `sys.exit` is called when the file does not exist.
- `sys.exit` is called when the file contains invalid JSON.
- `sys.exit` is called when the top-level JSON value is not a dict.
- An error message is printed to stderr on file-not-found.
- An error message is printed to stderr on invalid JSON.
- An error message is printed to stderr when the JSON is not a dict.

#### `TestWriteFile`

Tests for `write_file(file_path, content)`:

- The given content is written to the specified file.
- Missing parent directories are created automatically.
- Writing to an existing file overwrites its content.
- An empty string can be written without error.
- Multiline content is written correctly.

---

### Replacement Utils Tests (`test_replacement_utils.py`)

Tests for `ReplacementUtils` in `utils/replacement_utils.py`.

#### `TestNormalizeWhitespace`

Tests for `normalize_whitespace(text)`:

- Non-breaking spaces (`\xa0`) are replaced with regular spaces.
- Three or more consecutive newlines are collapsed to two.
- Leading and trailing whitespace is stripped.
- Plain text with no special whitespace is returned unchanged.

## Example Test Run Output

```
========================= test session starts ==========================
platform ...
collected N items

tests/test_convert_intro_to_md.py ......................
tests/test_file_utils.py ...........
tests/test_replacement_utils.py ......

========================== N passed in Xs ============================
```


This directory contains tests for `convert_intro_to_md.py` and its utility modules under `utils/`.

## Project Structure

```
convert_intro_to_md/
├── convert_intro_to_md.py    # Main script: orchestrates JSON → Markdown conversion
├── utils/
│   ├── __init__.py
│   ├── file_utils.py         # File I/O: reading JSON, writing Markdown
│   ├── html_utils.py         # HTML grouping, conversion, and note parsing
│   ├── processing_utils.py   # Block content, notes, and Markdown assembly pipeline
│   └── replacement_utils.py  # Tokenization and detokenization of special HTML constructs
├── tests/
│   ├── data/
│   │   ├── intro.json
│   │   ├── intro_de.md
│   │   └── intro_en.md
│   ├── __init__.py
│   ├── test_convert_intro_to_md.py
│   ├── test_file_utils.py
│   ├── test_html_utils.py
│   ├── test_processing_utils.py
│   └── test_replacement_utils.py
├── requirements.txt
└── pytest.ini
```

## Setup

See the [Virtual Environments](../../README.md#virtual-environments) section in the repo-level README for how to create and activate a virtual environment.

Once the virtual environment is active, install dependencies:

```bash
pip install -r requirements.txt --require-hashes
```

## Running Tests

```bash
# Run all tests
pytest .

# Run with verbose output
pytest . -v

# Run a specific test module
pytest tests/test_html_utils.py -v
```

## Coverage

```bash
# Run with coverage (configured in pytest.ini)
pytest . --cov=utils --cov=convert_intro_to_md --cov-report=html --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

Test modules are listed alphabetically.

---

### Main Script Tests (`test_convert_intro_to_md.py`)

Tests for the three public functions in `convert_intro_to_md.py`.

#### `TestConvertIntroToMd`

Tests for `convert_intro_to_md(intro, intro_locale)`:

- Returns a string for any valid intro dict.
- An intro with no content blocks produces a bare newline.
- Block headers are rendered as `## <header>` lines.
- Null or whitespace-only block headers are skipped.
- `blockContent` is routed through `ProcessingUtils.process_block_content`.
- `blockNotes` are routed through `ProcessingUtils.process_block_notes`.
- Collected notes are passed to `ProcessingUtils.process_end_notes` with the locale.
- Final lines are assembled via `ProcessingUtils.assemble_markdown`.
- A missing `content` key is handled gracefully.

#### `TestGetIntroContext`

Tests for `get_intro_context(intro, output_path)`:

- The locale is extracted as the segment before the first hyphen in the id.
- The full intro id is returned unchanged.
- The output path has the locale appended before the file extension.
- An id with no hyphen is used directly as the locale.
- A missing id leaves the output path unchanged.
- The output file is placed in the same directory as the base path.

#### `TestMain`

Tests for `main()`:

- Exits with code 1 when no arguments are provided.
- Prints a usage example to stderr when no args are given.
- Exits when the JSON has no `intro` key.
- Prints an error message to stderr when the intro array is missing.
- Writes an output file for each intro entry.
- Writes one file per locale for multi-locale input.
- Prints `Converted:` and `Written:` lines for each processed intro.

---

### File Utils Tests (`test_file_utils.py`)

Tests for `FileUtils` in `utils/file_utils.py`.

#### `TestReadJson`

Tests for `read_json(file_path)`:

- A valid JSON file is read and returned as a dict.
- Nested JSON structures are parsed correctly.
- `sys.exit` is called when the file does not exist.
- `sys.exit` is called when the file contains invalid JSON.
- `sys.exit` is called when the top-level JSON value is not a dict.
- An error message is printed to stderr on file-not-found.
- An error message is printed to stderr on invalid JSON.
- An error message is printed to stderr when the JSON is not a dict.

#### `TestWriteFile`

Tests for `write_file(file_path, content)`:

- The given content is written to the specified file.
- Missing parent directories are created automatically.
- Writing to an existing file overwrites its content.
- An empty string can be written without error.
- Multiline content is written correctly.

---

### HTML Utils Tests (`test_html_utils.py`)

Tests for `HTMLUtils` in `utils/html_utils.py`.
Uses `# pylint: disable=protected-access` to test private helpers directly.

#### `TestGroupBlockContent`

Tests for `group_block_content(block_content)`:

- Regular paragraphs are passed through unchanged.
- A single small paragraph is wrapped in a `<blockquote>`.
- Consecutive small paragraphs are combined into one `<blockquote>`.
- Two separate runs of small paragraphs produce two `<blockquote>` elements.
- A `<p>` with both `small` and `list` classes is not treated as small.
- An empty input list returns an empty list.
- The order of items is preserved in the output.
- Delegates detection to `_is_small_para` and grouping to `_combine_small_paras`.

#### `TestHtmlToMd`

Tests for `html_to_md(html)`:

- Plain paragraphs, bold, and headings are converted to Markdown.
- Angular event bindings are stripped before conversion.
- Footnote reference anchors are converted to Markdown footnote refs `[^N]`.
- Cross-reference anchors are converted to inline links `[N](#fnN)`.
- Pipe characters in text are converted to escaped Markdown pipes `\|`.
- Empty string and non-string input return an empty string.

#### `TestParseBlockNote`

Tests for `parse_block_note(note_html)`:

- Returns a `(note_number, stripped_html)` tuple for a valid blockNote.
- Both single-quoted and double-quoted id attributes are parsed.
- Returns `None` when no note id is present.
- The backlink anchor and pipe separator are stripped from the result.
- Return value is a `tuple`, not a list.
- Delegates to `_extract_note_number` and `_strip_note_html`.

---

### Processing Utils Tests (`test_processing_utils.py`)

Tests for `ProcessingUtils` in `utils/processing_utils.py`.

#### `TestAssembleMarkdown`

Tests for `assemble_markdown(md_lines)`:

- Lines are joined with newline separators.
- The result always ends with a trailing newline.
- Three or more consecutive newlines are collapsed to two.
- An empty line list produces a single newline.

#### `TestProcessBlockContent`

Tests for `process_block_content(block_content)`:

- An empty input list produces an empty output list.
- Items are routed through `HTMLUtils.group_block_content`.
- Each grouped item is converted via `HTMLUtils.html_to_md`.
- Each converted entry is followed by a blank line.
- Items that convert to an empty string are omitted from output.

#### `TestProcessBlockNotes`

Tests for `process_block_notes(block_notes, notes)`:

- An empty input list does not modify the notes dict.
- Each note string is parsed via `HTMLUtils.parse_block_note`.
- A successfully parsed note is added to the notes dict.
- Multiple block notes are all parsed and added.
- Notes for which `parse_block_note` returns `None` are ignored.
- A duplicate note number preserves the first value.
- A message is printed to stderr when a duplicate note number is encountered.

#### `TestProcessEndNotes`

Tests for `process_end_notes(notes, locale)`:

- An empty notes dict produces no output.
- The English locale produces a `## Notes` section header.
- Non-English locales produce a `## Anmerkungen` header.
- The section starts with a horizontal rule `---`.
- Each note's HTML is converted via `HTMLUtils.html_to_md`.
- Each note line is formatted as `[^N]: | <content>`.
- Notes are output in ascending numeric order.
- Each note entry is followed by a blank line.

---

### Replacement Utils Tests (`test_replacement_utils.py`)

Tests for `ReplacementUtils` in `utils/replacement_utils.py`.
Uses `# pylint: disable=protected-access` to test private helpers directly.

#### `TestNormalizeWhitespace`

Tests for `normalize_whitespace(text)`:

- Non-breaking spaces (`\xa0`) are replaced with regular spaces.
- Three or more consecutive newlines are collapsed to two.
- Leading and trailing whitespace is stripped.
- Plain text with no special whitespace is returned unchanged.

#### `TestDetokenize`

Tests for `detokenize(text)`:

- All token types are restored in a single call.
- `FNREF` tokens are restored to Markdown footnote refs `[^N]`.
- `FNCROSSREF` tokens are restored to inline links `[N](#fnN)`.
- `PIPE` tokens are restored to escaped Markdown pipes `\|`.
- Markdownify-escaped brackets `\[` and `\]` are unescaped.
- `tokenize` followed by `detokenize` is a consistent roundtrip for pipes.
- Plain text and empty strings are returned unchanged.

#### `TestTokenize`

Tests for `tokenize(html)`:

- All tokenizations are applied in a single call.
- Cross-reference anchors are tokenized to `FNCROSSREF` tokens.
- Footnote anchors are tokenized to `FNREF` tokens.
- Pipe characters are tokenized to `PIPE` tokens.
- Plain text and empty strings are returned unchanged.

## Example Test Run Output

```
========================= test session starts ==========================
platform ...
collected N items

tests/test_convert_intro_to_md.py ......................
tests/test_file_utils.py ...........
tests/test_html_utils.py .............................................
tests/test_processing_utils.py ........................
tests/test_replacement_utils.py ............................................

========================== N passed in Xs ============================
```
