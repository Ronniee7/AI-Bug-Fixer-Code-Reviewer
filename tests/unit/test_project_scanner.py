from pathlib import Path

import pytest

from app.services.project_scanner import ProjectScanner, UnsafeProjectPathError


def test_inspects_python_project_and_finds_risky_calls(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "sample"
    project.mkdir(parents=True)
    (project / "main.py").write_text("def run(x):\n    eval(x)\n", encoding="utf-8")

    result = ProjectScanner(workspace).inspect("sample")

    assert result.python_files == 1
    assert result.total_lines == 2
    assert any(item.rule_id == "PY-RISK-001" for item in result.diagnostics)


def test_reports_syntax_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "broken"
    project.mkdir(parents=True)
    (project / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    result = ProjectScanner(workspace).inspect("broken")

    assert any(item.rule_id == "PY-SYNTAX-001" for item in result.diagnostics)


def test_rejects_path_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    scanner = ProjectScanner(workspace)

    with pytest.raises(UnsafeProjectPathError):
        scanner.inspect("../outside")
