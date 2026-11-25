from typing import Literal

from pydantic import BaseModel

Severity = Literal["critical", "high", "medium", "low", "info"]
Confidence = Literal["high", "medium", "low"]


class Finding(BaseModel):
    rule_id: str
    tool: str
    severity: Severity
    confidence: Confidence
    message: str
    file_path: str
    line: int | None = None
    column: int | None = None
    evidence: str | None = None
    recommendation: str | None = None


class ToolStatus(BaseModel):
    name: str
    status: Literal["completed", "not_installed", "failed"]
    findings_count: int = 0
    duration_ms: int = 0
    message: str | None = None


class AnalysisResponse(BaseModel):
    project_path: str
    files_analyzed: int
    total_findings: int
    findings: list[Finding]
    tools: list[ToolStatus]
