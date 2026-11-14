from fastapi import APIRouter, HTTPException, Query
from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse
from app.services.static_analysis_service import StaticAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(project_path: str = Query(min_length=1, max_length=500)) -> AnalysisResponse:
    try:
        return StaticAnalysisService(get_settings()).analyze(project_path)
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
