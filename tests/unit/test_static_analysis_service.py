from pathlib import Path
from app.core.config import Settings
from app.services.static_analysis_service import StaticAnalysisService


def test_analysis_returns_normalized_ast_finding(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "demo"
    project.mkdir(parents=True)
    (project / "main.py").write_text("def f(value):\n    eval(value)\n", encoding="utf-8")
    result = StaticAnalysisService(Settings(workspace_root=workspace)).analyze("demo")
    assert result.files_analyzed == 1
    assert result.total_findings >= 1
    assert any(f.rule_id == "PY-RISK-001" for f in result.findings)
    assert {tool.name for tool in result.tools} == {"python_ast", "ruff", "bandit"}
