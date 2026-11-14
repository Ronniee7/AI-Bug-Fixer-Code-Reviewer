from pydantic import BaseModel, Field


class ProjectInspectRequest(BaseModel):
    project_path: str = Field(min_length=1, max_length=500)


class Diagnostic(BaseModel):
    rule_id: str
    severity: str
    message: str
    file_path: str
    line: int | None = None
    evidence: str | None = None


class ProjectInspectResponse(BaseModel):
    project_path: str
    python_files: int
    total_lines: int
    total_bytes: int
    diagnostics: list[Diagnostic]
    skipped_files: int
