import json
import shutil
import subprocess
import time
from pathlib import Path

from app.schemas.analysis import Finding, ToolStatus

LEVEL = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}


class BanditAnalyzer:
    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds

    def analyze(self, project: Path) -> tuple[list[Finding], ToolStatus]:
        if shutil.which("bandit") is None:
            return [], ToolStatus(
                name="bandit",
                status="not_installed",
                message="Bandit is not installed in this environment.",
            )
        started = time.perf_counter()
        try:
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    ".",
                    "-f",
                    "json",
                    "-q",
                    "-x",
                    ".git,.venv,venv,__pycache__,node_modules,dist,build",
                ],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
            if result.returncode not in (0, 1):
                raise RuntimeError((result.stderr or result.stdout)[-2000:])
            payload = json.loads(result.stdout or "{}")
            findings = []
            for item in payload.get("results", []):
                findings.append(
                    Finding(
                        rule_id=item.get("test_id", "BANDIT"),
                        tool="bandit",
                        severity=LEVEL.get(str(item.get("issue_severity", "LOW")).upper(), "low"),
                        confidence=LEVEL.get(
                            str(item.get("issue_confidence", "LOW")).upper(), "low"
                        ),
                        message=item.get("issue_text", "Bandit security finding"),
                        file_path=str(item.get("filename", "")).replace("\\", "/"),
                        line=item.get("line_number"),
                        evidence=item.get("code"),
                        recommendation=item.get("more_info"),
                    )
                )
            return findings, ToolStatus(
                name="bandit",
                status="completed",
                findings_count=len(findings),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        except subprocess.TimeoutExpired:
            message = f"Bandit exceeded {self.timeout_seconds} seconds."
        except (OSError, ValueError, RuntimeError) as exc:
            message = str(exc)
        return [], ToolStatus(
            name="bandit",
            status="failed",
            duration_ms=int((time.perf_counter() - started) * 1000),
            message=message,
        )
