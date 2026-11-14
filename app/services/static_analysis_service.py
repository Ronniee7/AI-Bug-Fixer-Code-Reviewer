from pathlib import Path
from app.analyzers.bandit_analyzer import BanditAnalyzer
from app.analyzers.ruff_analyzer import RuffAnalyzer
from app.core.config import Settings
from app.schemas.analysis import AnalysisResponse, Finding, ToolStatus
from app.services.project_scanner import ProjectScanner


class StaticAnalysisService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scanner = ProjectScanner(
            settings.workspace_root, settings.max_files_per_scan, settings.max_file_size_bytes
        )
        self.ruff = RuffAnalyzer()
        self.bandit = BanditAnalyzer()

    def analyze(self, project_path: str) -> AnalysisResponse:
        project = self._resolve_project(project_path)
        inventory = self.scanner.inspect(project_path)
        findings = [
            Finding(
                rule_id=d.rule_id,
                tool="python_ast",
                severity=self._severity(d.severity),
                confidence="high",
                message=d.message,
                file_path=d.file_path,
                line=d.line,
                evidence=d.evidence,
                recommendation="Inspect this source location and address the underlying issue.",
            )
            for d in inventory.diagnostics
        ]
        ruff_findings, ruff_status = self.ruff.analyze(project)
        bandit_findings, bandit_status = self.bandit.analyze(project)
        findings.extend(ruff_findings)
        findings.extend(bandit_findings)
        findings = self._deduplicate(findings)
        ast_count = sum(f.tool == "python_ast" for f in findings)
        return AnalysisResponse(
            project_path=project_path,
            files_analyzed=inventory.python_files,
            total_findings=len(findings),
            findings=findings,
            tools=[
                ToolStatus(name="python_ast", status="completed", findings_count=ast_count),
                ruff_status,
                bandit_status,
            ],
        )

    def _resolve_project(self, project_path: str) -> Path:
        root = self.settings.workspace_root.expanduser().resolve()
        candidate = (root / project_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Project path must remain inside WORKSPACE_ROOT.") from exc
        if not candidate.exists():
            raise FileNotFoundError(f"Project does not exist: {project_path}")
        if not candidate.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {project_path}")
        return candidate

    @staticmethod
    def _severity(value: str) -> str:
        return {
            "error": "high",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
        }.get(value.lower(), "medium")

    @staticmethod
    def _deduplicate(items: list[Finding]) -> list[Finding]:
        unique = {}
        for item in items:
            key = (item.tool, item.rule_id, item.file_path, item.line, item.message)
            unique[key] = item
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        return sorted(
            unique.values(), key=lambda f: (order.get(f.severity, 5), f.file_path, f.line or 0)
        )
