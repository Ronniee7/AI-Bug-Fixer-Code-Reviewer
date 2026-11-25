import json
import shutil
import subprocess
import time
from pathlib import Path

from app.schemas.analysis import Finding, ToolStatus

SEVERITY = {"E": "medium", "F": "high", "W": "low", "I": "low", "B": "medium"}


class RuffAnalyzer:
    def __init__(self, timeout_seconds: int = 45) -> None:
        self.timeout_seconds = timeout_seconds

    def analyze(self, project: Path) -> tuple[list[Finding], ToolStatus]:
        if shutil.which("ruff") is None:
            return [], ToolStatus(
                name="ruff",
                status="not_installed",
                message="Ruff is not installed in this environment.",
            )
        started = time.perf_counter()
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format", "json", "."],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
            if result.returncode not in (0, 1):
                raise RuntimeError((result.stderr or result.stdout)[-2000:])
            raw = json.loads(result.stdout or "[]")
            findings = []
            for item in raw:
                code = item.get("code") or "RUFF"
                loc = item.get("location") or {}
                findings.append(
                    Finding(
                        rule_id=code,
                        tool="ruff",
                        severity=SEVERITY.get(code[:1], "low"),
                        confidence="high",
                        message=item.get("message", "Ruff diagnostic"),
                        file_path=str(item.get("filename", "")).replace("\\", "/"),
                        line=loc.get("row"),
                        column=loc.get("column"),
                        evidence=code,
                        recommendation=(
                            "Review the diagnostic; apply an automatic fix only"
                             "after inspecting the diff."
                        ),
                    )
                )
            return findings, ToolStatus(
                name="ruff",
                status="completed",
                findings_count=len(findings),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        except subprocess.TimeoutExpired:
            message = f"Ruff exceeded {self.timeout_seconds} seconds."
        except (OSError, ValueError, RuntimeError) as exc:
            message = str(exc)
        return [], ToolStatus(
            name="ruff",
            status="failed",
            duration_ms=int((time.perf_counter() - started) * 1000),
            message=message,
        )
