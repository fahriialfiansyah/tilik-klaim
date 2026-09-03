"""`GET /healthz` — liveness for the platform, readiness for the presenter.

The two are deliberately not the same answer. `railway.json` points its platform health probe at
this path, so the **HTTP status never depends on the database**: a probe that failed when Postgres
blipped would restart the container in a loop exactly when the database is already struggling,
and the backend is designed to run without one at all so the demo can be rehearsed offline.

So the response is always `200` with `status: ok` while the process is alive, and the `readiness`
block underneath says whether the ninety-second flow would actually work.
`scripts/demo_reset.py --check` reads that block and is what exits non-zero.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.service.briefing.service import is_llm_configured, list_gateway_models
from app.service.demo_state import check_readiness
from app.service.llm_provider import LlmUnavailable

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, object]:
    """Liveness, the engine identity the runbook quotes, and demo readiness."""
    readiness = check_readiness()
    return {
        "status": "ok",
        "engine_version": readiness.engine_version,
        "ruleset_version": readiness.ruleset_version,
        "dataset_version": readiness.dataset_version,
        "data_class": "synthetic",
        "readiness": readiness.as_payload(),
    }


@router.get("/health/llm")
def health_llm(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    """Does the briefing gateway answer, and does it hold the model that was configured?

    Deliberately **not** part of `/healthz`: the platform probes that path, and a health check
    that failed because an optional summariser was unreachable would restart the container over
    a feature the product does not require.

    Listing models tests the network and the credential at once without spending a token, and
    `model_available: false` catches a mistyped model name before a reviewer's first click
    rather than during a demo. The key is never in the response — `SecretStr` sees to that.
    """
    if not is_llm_configured(settings):
        # Off is a supported, documented configuration, not a degraded one.
        return {
            "configured": False,
            "detail": "BRIEFING_ENABLED is false or the gateway is unconfigured; "
            "briefings are produced by the deterministic template.",
        }

    try:
        available = list_gateway_models(settings)
    except LlmUnavailable as unreachable:
        raise HTTPException(status_code=503, detail=str(unreachable)) from unreachable

    return {
        "configured": True,
        "base_url": settings.vllm_base_url,
        "model": settings.llm_model_vllm,
        "model_available": settings.llm_model_vllm in available,
        "model_count": len(available),
    }
