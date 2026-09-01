"""`GET /healthz` — liveness for the platform, readiness for the presenter.

The two are deliberately not the same answer. `railway.json` points its platform health probe at
this path, so the **HTTP status never depends on the database**: a probe that failed when Postgres
blipped would restart the container in a loop exactly when the database is already struggling,
and the backend is designed to run without one at all so the demo can be rehearsed offline.

So the response is always `200` with `status: ok` while the process is alive, and the `readiness`
block underneath says whether the ninety-second flow would actually work.
`scripts/demo_reset.py --check` reads that block and is what exits non-zero.
"""
from fastapi import APIRouter

from app.service.demo_state import check_readiness

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
