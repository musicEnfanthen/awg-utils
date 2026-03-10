"""Tests for unify_link_box_ids.py."""

from unittest.mock import call

import pytest

import unify_link_box_ids as module_under_test
from unify_link_box_ids import (
    main,
    process_single_link_box,
    process_textcritics_entry,
    unify_link_box_ids,
)


@pytest.fixture(name="sample_svg_data")
def fixture_sample_svg_data():
    """Return mutable SVG data."""
    return {"content": "<svg-content>"}


class TestProcessSingleLinkBox:
    """Tests for process_single_link_box."""

    def test_process_single_link_box_with_success(
        self, mocker, capsys, sample_svg_data
    ):
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M_317_Sk2"}}
        get_svg_data = mocker.Mock(return_value=sample_svg_data)
        update_mock = mocker.patch.object(
            module_under_test,
            "update_svg_id_by_class",
            return_value=("<updated-svg-content>", None),
        )

        result = process_single_link_box(
            "g6407", link_box, "op25_WE", ["sheet.svg"], get_svg_data
        )

        expected_new_id = "g-lb-op25_we-to-m_317_sk2"

        assert result is True
        assert link_box["svgGroupId"] == expected_new_id
        get_svg_data.assert_called_once_with("sheet.svg")
        update_mock.assert_called_once_with(
            "<svg-content>",
            "g6407",
            expected_new_id,
            "link-box",
        )
        assert sample_svg_data["content"] == "<updated-svg-content>"

        output = capsys.readouterr().out
        assert f"[JSON] Changing 'g6407' -> '{expected_new_id}'" in output
        assert f"[SVG] Changing 'g6407' -> '{expected_new_id}' in sheet.svg" in output

    def test_process_single_link_box_with_no_matching_files(self, mocker, capsys):
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M_317_Sk2"}}
        get_svg_data = mocker.Mock()

        result = process_single_link_box("g6407", link_box, "op25_WE", [], get_svg_data)

        assert result is False
        assert link_box["svgGroupId"] == "g6407"
        get_svg_data.assert_not_called()
        output = capsys.readouterr().out
        assert "not found in any relevant SVG files" in output

    def test_process_single_link_box_with_multiple_matching_files(self, mocker, capsys):
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M_317_Sk2"}}
        get_svg_data = mocker.Mock()

        result = process_single_link_box(
            "g6407",
            link_box,
            "op25_WE",
            ["a.svg", "b.svg"],
            get_svg_data,
        )

        assert result is False
        assert link_box["svgGroupId"] == "g6407"
        get_svg_data.assert_not_called()
        output = capsys.readouterr().out
        assert "found in 2 files" in output
        assert "Skipping due to multiple occurrences" in output

    def test_process_single_link_box_with_missing_sheet_id(self, mocker, capsys):
        link_box = {"svgGroupId": "g6407", "linkTo": {}}
        get_svg_data = mocker.Mock()

        result = process_single_link_box(
            "g6407", link_box, "op25_WE", ["sheet.svg"], get_svg_data
        )

        assert result is False
        assert link_box["svgGroupId"] == "g6407"
        get_svg_data.assert_not_called()
        output = capsys.readouterr().out
        assert "No sheetId found in linkBox with svgGroupId 'g6407'" in output

    def test_process_single_link_box_with_svg_update_error(
        self, mocker, capsys, sample_svg_data
    ):
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M_317_Sk2"}}
        get_svg_data = mocker.Mock(return_value=sample_svg_data)
        mocker.patch.object(
            module_under_test,
            "update_svg_id_by_class",
            return_value=("<svg-content>", "Could not update id"),
        )

        result = process_single_link_box(
            "g6407", link_box, "op25_WE", ["sheet.svg"], get_svg_data
        )

        expected_new_id = "g-lb-op25_we-to-m_317_sk2"

        assert result is False
        # Current behavior: JSON id changes before SVG update failure is returned.
        assert link_box["svgGroupId"] == expected_new_id
        output = capsys.readouterr().out
        assert "WARNING: Could not update id" in output


class TestProcessTextcriticsEntry:
    """Tests for process_textcritics_entry."""

    def test_process_textcritics_entry_returns_for_non_dict(self, mocker):
        extract_number_mock = mocker.patch.object(
            module_under_test, "extract_moldenhauer_number"
        )

        process_textcritics_entry("not-a-dict", ["a.svg"], mocker.Mock())

        extract_number_mock.assert_not_called()

    def test_process_textcritics_entry_returns_when_id_missing(self, mocker):
        extract_number_mock = mocker.patch.object(
            module_under_test, "extract_moldenhauer_number"
        )

        process_textcritics_entry({}, ["a.svg"], mocker.Mock())

        extract_number_mock.assert_not_called()

    def test_process_textcritics_entry_success_basic(self, mocker, capsys):
        entry = {"id": "M_143_TF1"}
        all_svg_files = ["test1.svg", "test2.svg"]
        link_boxes = [
            {"svgGroupId": "g1", "linkTo": {"sheetId": "M_143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M_143_Sk2"}},
        ]
        get_svg_data = mocker.Mock()

        extract_number_mock = mocker.patch.object(
            module_under_test, "extract_moldenhauer_number", return_value="143"
        )
        find_relevant_mock = mocker.patch.object(
            module_under_test,
            "find_relevant_svg_files",
            return_value=["test1.svg", "test2.svg"],
        )
        extract_link_boxes_mock = mocker.patch.object(
            module_under_test, "extract_link_boxes", return_value=link_boxes
        )
        find_matching_mock = mocker.patch.object(
            module_under_test,
            "find_matching_svg_files_by_class",
            side_effect=[["test1.svg"], ["test2.svg"]],
        )
        process_single_mock = mocker.patch.object(
            module_under_test, "process_single_link_box", return_value=True
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        extract_number_mock.assert_called_once_with("M_143_TF1")
        find_relevant_mock.assert_called_once_with("M_143_TF1", all_svg_files, "143")
        extract_link_boxes_mock.assert_called_once_with(entry)
        assert find_matching_mock.call_args_list == [
            call("g1", ["test1.svg", "test2.svg"], get_svg_data, "link-box"),
            call("g2", ["test1.svg", "test2.svg"], get_svg_data, "link-box"),
        ]
        assert process_single_mock.call_args_list == [
            call("g1", link_boxes[0], "M_143_TF1", ["test1.svg"], get_svg_data),
            call("g2", link_boxes[1], "M_143_TF1", ["test2.svg"], get_svg_data),
        ]

        output = capsys.readouterr().out
        assert "Processing textcritics entry ID: M_143_TF1" in output
        assert "Standard anchor: M_143_TF1" in output
        assert "Relevant SVGs (2): ['test1.svg', 'test2.svg']" in output
        assert "Found 2 linkBox(es)" in output

    def test_process_textcritics_entry_prints_skrt_anchor_and_no_link_boxes(
        self, mocker, capsys
    ):
        entry = {"id": "M_143_SkRT1"}
        all_svg_files = ["test1.svg"]
        get_svg_data = mocker.Mock()

        mocker.patch.object(
            module_under_test, "extract_moldenhauer_number", return_value="143"
        )
        mocker.patch.object(
            module_under_test,
            "find_relevant_svg_files",
            return_value=["test1.svg"],
        )
        mocker.patch.object(module_under_test, "extract_link_boxes", return_value=[])
        find_matching_mock = mocker.patch.object(
            module_under_test, "find_matching_svg_files_by_class"
        )
        process_single_mock = mocker.patch.object(
            module_under_test, "process_single_link_box"
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        find_matching_mock.assert_not_called()
        process_single_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "SkRT anchor detected: M_143_SkRT1" in output
        assert "No linkBoxes to process" in output

    def test_process_textcritics_entry_skips_link_box_without_svg_group_id(
        self, mocker, capsys
    ):
        entry = {"id": "M_143_TF1"}
        all_svg_files = ["sheet.svg"]
        link_boxes = [
            {"linkTo": {"sheetId": "M_143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M_143_Sk2"}},
        ]
        get_svg_data = mocker.Mock()

        mocker.patch.object(
            module_under_test, "extract_moldenhauer_number", return_value="143"
        )
        mocker.patch.object(
            module_under_test,
            "find_relevant_svg_files",
            return_value=["sheet.svg"],
        )
        mocker.patch.object(module_under_test, "extract_link_boxes", return_value=link_boxes)
        find_matching_mock = mocker.patch.object(
            module_under_test,
            "find_matching_svg_files_by_class",
            return_value=["sheet.svg"],
        )
        process_single_mock = mocker.patch.object(
            module_under_test, "process_single_link_box", return_value=True
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        find_matching_mock.assert_called_once_with(
            "g2", ["sheet.svg"], get_svg_data, "link-box"
        )
        process_single_mock.assert_called_once_with(
            "g2", link_boxes[1], "M_143_TF1", ["sheet.svg"], get_svg_data
        )
        output = capsys.readouterr().out
        assert "ERROR: linkBox without svgGroupId" in output


class TestUnifyLinkBoxIds:
    """Tests for unify_link_box_ids."""

    def test_unify_link_box_ids_processes_dict_textcritics(self, mocker, capsys):
        json_data = {"textcritics": [{"id": "A"}, {"id": "B"}]}
        all_svg_files = ["A.svg", "B.svg"]
        get_svg_data = mocker.Mock(name="get_svg_data")
        captured = {}

        load_mock = mocker.patch.object(
            module_under_test,
            "load_and_validate_inputs",
            return_value=(json_data, all_svg_files),
        )

        def _fake_create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts):
            captured["svg_folder"] = svg_folder
            captured["final_svg_cache"] = final_svg_cache
            captured["loaded_svg_texts"] = loaded_svg_texts
            return get_svg_data

        create_loader_mock = mocker.patch.object(
            module_under_test,
            "create_svg_loader",
            side_effect=_fake_create_svg_loader,
        )
        process_entry_mock = mocker.patch.object(module_under_test, "process_textcritics_entry")
        save_results_mock = mocker.patch.object(module_under_test, "save_results")

        result = unify_link_box_ids("textcritics.json", "img/")

        assert result is True
        load_mock.assert_called_once_with("textcritics.json", "img/")
        create_loader_mock.assert_called_once()
        assert captured["svg_folder"] == "img/"
        assert captured["final_svg_cache"] == {}
        assert captured["loaded_svg_texts"] == {}
        assert process_entry_mock.call_args_list == [
            call({"id": "A"}, all_svg_files, get_svg_data),
            call({"id": "B"}, all_svg_files, get_svg_data),
        ]
        save_results_mock.assert_called_once_with(
            json_data, captured["loaded_svg_texts"], "textcritics.json"
        )

        output = capsys.readouterr().out
        assert "--- Starting Link Box ID processing ---" in output
        assert "--- Link Box ID processing completed ---" in output

    def test_unify_link_box_ids_processes_list_root(self, mocker):
        json_data = [{"id": "A"}, {"id": "B"}]
        all_svg_files = ["A.svg"]
        get_svg_data = mocker.Mock(name="get_svg_data")

        mocker.patch.object(
            module_under_test,
            "load_and_validate_inputs",
            return_value=(json_data, all_svg_files),
        )
        mocker.patch.object(
            module_under_test,
            "create_svg_loader",
            return_value=get_svg_data,
        )
        process_entry_mock = mocker.patch.object(module_under_test, "process_textcritics_entry")
        save_results_mock = mocker.patch.object(module_under_test, "save_results")

        result = unify_link_box_ids("textcritics.json", "img/")

        assert result is True
        assert process_entry_mock.call_args_list == [
            call({"id": "A"}, all_svg_files, get_svg_data),
            call({"id": "B"}, all_svg_files, get_svg_data),
        ]
        save_results_mock.assert_called_once_with(json_data, {}, "textcritics.json")


class TestMain:
    """Tests for main."""

    def test_main_success_path(self, mocker, capsys):
        process_mock = mocker.patch.object(
            module_under_test, "unify_link_box_ids", return_value=True
        )
        exit_mock = mocker.patch.object(module_under_test.sys, "exit")

        main()

        process_mock.assert_called_once_with(
            "./tests/data/textcritics.json", "./tests/img/"
        )
        exit_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "Finished!" in output

    def test_main_with_warnings(self, mocker, capsys):
        process_mock = mocker.patch.object(
            module_under_test, "unify_link_box_ids", return_value=False
        )
        exit_mock = mocker.patch.object(module_under_test.sys, "exit")

        main()

        process_mock.assert_called_once_with(
            "./tests/data/textcritics.json", "./tests/img/"
        )
        exit_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "Processing completed with warnings." in output

    def test_main_handles_file_not_found(self, mocker, capsys):
        mocker.patch.object(
            module_under_test,
            "unify_link_box_ids",
            side_effect=FileNotFoundError("missing-file"),
        )
        exit_mock = mocker.patch.object(module_under_test.sys, "exit")

        main()

        exit_mock.assert_called_once_with(1)
        output = capsys.readouterr().out
        assert "Error: missing-file" in output

    def test_main_handles_unexpected_error(self, mocker, capsys):
        mocker.patch.object(
            module_under_test,
            "unify_link_box_ids",
            side_effect=ValueError("bad-config"),
        )
        exit_mock = mocker.patch.object(module_under_test.sys, "exit")

        main()

        exit_mock.assert_called_once_with(1)
        output = capsys.readouterr().out
        assert "Unexpected error: bad-config" in output
