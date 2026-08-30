from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe. Also surfaces the engine identity used by the demo runbook."""
    settings = get_settings()
    return {
        "status": "ok",
        "engine_version": settings.engine_version,
        "ruleset_version": settings.ruleset_version,
        "dataset_version": settings.dataset_version,
        "data_class": "synthetic",
    }
