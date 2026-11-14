from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.project import ProjectInspectRequest, ProjectInspectResponse
from app.services.project_scanner import ProjectScanner, UnsafeProjectPathError

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/inspect", response_model=ProjectInspectResponse)
async def inspect_project(payload: ProjectInspectRequest) -> ProjectInspectResponse:
    settings = get_settings()
    scanner = ProjectScanner(
        workspace_root=settings.workspace_root,
        max_files=settings.max_files_per_scan,
        max_file_size_bytes=settings.max_file_size_bytes,
    )
    try:
        return scanner.inspect(payload.project_path)
    except (UnsafeProjectPathError, FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
