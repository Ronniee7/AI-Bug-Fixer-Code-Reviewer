import ast
from pathlib import Path

from app.schemas.project import Diagnostic, ProjectInspectResponse

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".tox",
}


class UnsafeProjectPathError(ValueError):
    """Raised when a requested project escapes the configured workspace."""


class ProjectScanner:
    def __init__(
        self,
        workspace_root: Path,
        max_files: int = 500,
        max_file_size_bytes: int = 262_144,
    ) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.max_files = max_files
        self.max_file_size_bytes = max_file_size_bytes

    def _resolve_project(self, project_path: str) -> Path:
        candidate = (self.workspace_root / project_path).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError as exc:
            raise UnsafeProjectPathError("Project path must remain inside WORKSPACE_ROOT.") from exc
        if not candidate.exists():
            raise FileNotFoundError(f"Project does not exist: {project_path}")
        if not candidate.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {project_path}")
        return candidate

    def inspect(self, project_path: str) -> ProjectInspectResponse:
        project = self._resolve_project(project_path)
        diagnostics: list[Diagnostic] = []
        python_files = 0
        total_lines = 0
        total_bytes = 0
        skipped_files = 0

        for path in self._python_files(project):
            if python_files + skipped_files >= self.max_files:
                skipped_files += 1
                continue
            try:
                size = path.stat().st_size
                if size > self.max_file_size_bytes:
                    skipped_files += 1
                    continue
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                skipped_files += 1
                continue

            python_files += 1
            total_bytes += size
            total_lines += len(source.splitlines())
            diagnostics.extend(self._analyze_file(path, project, source))

        return ProjectInspectResponse(
            project_path=project_path,
            python_files=python_files,
            total_lines=total_lines,
            total_bytes=total_bytes,
            diagnostics=diagnostics,
            skipped_files=skipped_files,
        )

    def _python_files(self, project: Path):
        for path in project.rglob("*.py"):
            if any(part in IGNORED_DIRS for part in path.relative_to(project).parts):
                continue
            if path.is_file():
                yield path

    def _analyze_file(self, path: Path, project: Path, source: str) -> list[Diagnostic]:
        relative_path = path.relative_to(project).as_posix()
        results: list[Diagnostic] = []
        try:
            tree = ast.parse(source, filename=relative_path)
        except SyntaxError as exc:
            results.append(
                Diagnostic(
                    rule_id="PY-SYNTAX-001",
                    severity="error",
                    message=exc.msg,
                    file_path=relative_path,
                    line=exc.lineno,
                    evidence=(exc.text or "").strip() or None,
                )
            )
            return results

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._call_name(node.func)
                if name in {"eval", "exec"}:
                    results.append(
                        Diagnostic(
                            rule_id="PY-RISK-001",
                            severity="high",
                            message=f"Use of {name}() can execute dynamically supplied code.",
                            file_path=relative_path,
                            line=node.lineno,
                            evidence=f"{name}(...)",
                        )
                    )
                if name == "Popen" and any(
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                ):
                    results.append(
                        Diagnostic(
                            rule_id="PY-RISK-002",
                            severity="high",
                            message="subprocess.Popen uses shell=True; review command construction.",
                            file_path=relative_path,
                            line=node.lineno,
                            evidence="Popen(..., shell=True)",
                        )
                    )
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                results.append(
                    Diagnostic(
                        rule_id="PY-QUALITY-001",
                        severity="medium",
                        message="Bare except catches every exception, including system-exiting exceptions.",
                        file_path=relative_path,
                        line=node.lineno,
                        evidence="except:",
                    )
                )

        return results

    @staticmethod
    def _call_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None
