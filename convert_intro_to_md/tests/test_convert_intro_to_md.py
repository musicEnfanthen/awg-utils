"""Tests for convert_intro_to_md.py"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from convert_intro_to_md import convert_intro_to_md, convert_intro_to_tei, get_intro_context, main
from utils import md_renderer, tei_renderer


class TestConvertIntroToMd:
    """Tests for the convert_intro_to_md function."""

    def test_delegates_to_md_renderer(self):
        """Test that convert_intro_to_md delegates to md_renderer.render."""
        blocks = []
        with patch.object(md_renderer, "render", return_value="done\n") as mock:
            result = convert_intro_to_md(blocks, "en")
        mock.assert_called_once_with(blocks, "en")
        assert result == "done\n"

    def test_passes_locale_to_renderer(self):
        """Test that the locale argument is forwarded unchanged to md_renderer.render."""
        with patch.object(md_renderer, "render", return_value="\n") as mock:
            convert_intro_to_md([], "de")
        mock.assert_called_once_with([], "de")


class TestConvertIntroToTei:
    """Tests for the convert_intro_to_tei function."""

    def test_delegates_to_tei_renderer(self):
        """Test that convert_intro_to_tei delegates to tei_renderer.render."""
        blocks = []
        with patch.object(tei_renderer, "render", return_value="<xml/>") as mock:
            result = convert_intro_to_tei(blocks, "de-1", "de")
        mock.assert_called_once_with(blocks, "de-1", "de")
        assert result == "<xml/>"

    def test_passes_all_args_to_renderer(self):
        """Test that blocks, intro_id and locale are all forwarded to tei_renderer.render."""
        with patch.object(tei_renderer, "render", return_value="<xml/>") as mock:
            convert_intro_to_tei([], "en-2", "en")
        mock.assert_called_once_with([], "en-2", "en")


class TestGetIntroContext:
    """Tests for the get_intro_context function."""

    def test_extracts_locale_from_id(self):
        """Test that the locale is the part before the first hyphen in the id."""
        _, locale, _ = get_intro_context({"id": "de-awg-I-5"}, Path("intro.md"))
        assert locale == "de"

    def test_extracts_id(self):
        """Test that the intro id is returned unchanged."""
        intro_id, _, _ = get_intro_context({"id": "en-awg-I-5"}, Path("intro.md"))
        assert intro_id == "en-awg-I-5"

    def test_output_path_includes_locale(self):
        """Test that the output path has the locale appended before the extension."""
        _, _, out = get_intro_context({"id": "de-awg-I-5"}, Path("intro.md"))
        assert out.name == "intro_de.md"

    def test_id_without_hyphen_uses_id_as_locale(self):
        """Test that an id with no hyphen is used directly as the locale."""
        _, locale, _ = get_intro_context({"id": "en"}, Path("intro.md"))
        assert locale == "en"

    def test_missing_id_falls_back_to_base_path(self):
        """Test that a missing id leaves the output path unchanged."""
        _, _, out = get_intro_context({}, Path("intro.md"))
        assert out.name == "intro.md"

    def test_preserves_output_directory(self):
        """Test that the output file is placed in the same directory as the base path."""
        _, _, out = get_intro_context({"id": "de-awg-I-5"}, Path("out/intro.md"))
        assert out.parent == Path("out")


class TestMain:
    """Tests for the main function."""

    def test_exits_with_no_args(self):
        """Test that main exits with code 1 when no arguments are provided."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1

    def test_prints_usage_hint_to_stderr(self, capsys):
        """Test that a usage example is printed to stderr when no args are given."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit):
                main()
        assert "Example:" in capsys.readouterr().err

    def test_exits_when_no_intro_array(self, tmp_path):
        """Test that main exits when the JSON has no 'intro' key."""
        f = tmp_path / "intro.json"
        f.write_text(json.dumps({}), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1

    def test_prints_no_intro_error_to_stderr(self, tmp_path, capsys):
        """Test that an error message is printed when the intro array is missing."""
        f = tmp_path / "intro.json"
        f.write_text(json.dumps({}), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            with pytest.raises(SystemExit):
                main()
        assert "No intro array" in capsys.readouterr().err

    def test_writes_output_file(self, tmp_path):
        """Test that main writes an output file for a given intro."""
        data = {"intro": [{"id": "de-awg-I-5", "content": []}]}
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        assert (tmp_path / "intro_de.md").exists()

    def test_writes_one_file_per_locale(self, tmp_path):
        """Test that main writes separate files for each locale in the intro array."""
        data = {
            "intro": [
                {"id": "de-awg-I-5", "content": []},
                {"id": "en-awg-I-5", "content": []},
            ]
        }
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        assert (tmp_path / "intro_de.md").exists()
        assert (tmp_path / "intro_en.md").exists()

    def test_prints_converted_and_written_lines(self, tmp_path, capsys):
        """Test that main prints 'Converted' and 'Written' lines for each intro."""
        data = {"intro": [{"id": "de-awg-I-5", "content": []}]}
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        out = capsys.readouterr().out
        assert "Converted:" in out
        assert "Written:" in out
