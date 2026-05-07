"""
Contract tests for the unifier modules (TKK, LinkBox, and KV).

This file verifies shared external behavior across all unifiers:
1) each module exports its expected public entry function, and
2) the CLI-style `main()` path handles missing files consistently
   by exiting with status code 1.

It intentionally does not validate unification logic internals;
those are covered in the unifier-specific test files.
"""

import importlib
import pytest


@pytest.mark.parametrize(
    "module_name,entry_fn",
    [
        ("unify_tkk_ids", "unify_tkk_ids"),
        ("unify_link_box_ids", "unify_link_box_ids"),
        ("unify_kv_ids", "unify_kv_ids"),
    ],
    ids=["tkk", "linkbox", "kv"],
)
def test_unifier_modules_export_entrypoint(module_name, entry_fn):
    "Test that each unifier module exports its expected public entry function"
    module = importlib.import_module(module_name)
    assert hasattr(module, entry_fn)
    assert callable(getattr(module, entry_fn))


@pytest.mark.parametrize(
    "module_name,entry_fn",
    [
        ("unify_tkk_ids", "unify_tkk_ids"),
        ("unify_link_box_ids", "unify_link_box_ids"),
        ("unify_kv_ids", "unify_kv_ids"),
    ],
    ids=["tkk", "linkbox", "kv"],
)
def test_main_handles_missing_file(module_name, entry_fn, mocker):
    "Test that unifier main() exits with code 1 when required files are missing"
    module = importlib.import_module(module_name)
    if not hasattr(module, "main") or not hasattr(module, "sys"):
        pytest.skip(f"{module_name} has no script-style main()")

    mocker.patch.object(module, entry_fn, side_effect=FileNotFoundError("missing"))
    exit_mock = mocker.patch.object(module.sys, "exit")
    mocker.patch.object(module.sys, "argv", ["prog"])

    module.main()

    exit_mock.assert_called_once_with(1)
