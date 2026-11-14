from fastapi import FastAPI
from app.api.routes.analysis import router as analysis_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Local-first AI code review and verified bug-fixing assistant.",
)
app.include_router(health_router)
app.include_router(projects_router, prefix=settings.api_v1_prefix)
app.include_router(analysis_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}
